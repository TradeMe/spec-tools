"""Markdown link validator for checking internal and external hyperlinks."""

import os
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pathspec


@dataclass
class Link:
    """Represents a hyperlink found in a markdown file."""

    text: str  # Link text
    url: str  # URL or path
    file_path: str  # Source markdown file (relative path)
    line_number: int  # Line number in source file
    is_external: bool = False  # Whether link is an external URL
    is_private: bool = False  # Whether link matches private URL pattern
    anchor: Optional[str] = None  # Anchor fragment (#heading)


@dataclass
class LinkValidationResult:
    """Result of link validation."""

    total_links: int
    valid_links: int
    invalid_links: int
    private_links: int
    skipped_links: int
    invalid_link_details: List[Dict[str, str]] = field(default_factory=list)
    markdown_files_checked: int = 0

    @property
    def is_valid(self) -> bool:
        """Returns True if all non-private links are valid."""
        return self.invalid_links == 0

    def __str__(self) -> str:
        """Human-readable summary of validation results."""
        lines = [
            f"Markdown files checked: {self.markdown_files_checked}",
            f"Total links found: {self.total_links}",
            f"Valid links: {self.valid_links}",
            f"Invalid links: {self.invalid_links}",
            f"Private links (skipped): {self.private_links}",
        ]

        if self.invalid_link_details:
            lines.append("\nInvalid links:")
            for detail in self.invalid_link_details:
                lines.append(
                    f"  - {detail['file']}:{detail['line']}: {detail['url']} ({detail['reason']})"
                )

        return "\n".join(lines)


class MarkdownLinkValidator:
    """Validates hyperlinks in markdown files.

    Checks internal links (relative paths) and external URLs.
    Supports private URL patterns that are skipped during validation.
    """

    DEFAULT_CONFIG_FILE = ".speclinkconfig"
    DEFAULT_IGNORE_FILE = ".gitignore"
    DEFAULT_TIMEOUT = 10  # seconds
    DEFAULT_MAX_CONCURRENT = 10

    # Regex patterns for finding markdown links
    # Matches: [text](url) and [text](url "title")
    INLINE_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)"\s]+)(?:\s+"[^"]*")?\)', re.MULTILINE)

    # Matches reference-style links: [text][ref] or [text]
    REFERENCE_LINK_PATTERN = re.compile(r"\[([^\]]+)\](?:\[([^\]]*)\])?", re.MULTILINE)

    # Matches reference definitions: [ref]: url
    REFERENCE_DEF_PATTERN = re.compile(r"^\[([^\]]+)\]:\s+(\S+)", re.MULTILINE)

    def __init__(
        self,
        root_dir: Optional[Path] = None,
        config_file: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        check_external: bool = True,
        use_gitignore: bool = True,
    ):
        """Initialize the validator.

        Args:
            root_dir: Root directory to scan. Defaults to current directory.
            config_file: Path to config file. Defaults to .speclinkconfig
            timeout: Timeout for external URL checks in seconds.
            max_concurrent: Maximum concurrent external URL requests.
            check_external: Whether to validate external URLs.
            use_gitignore: Whether to respect .gitignore patterns.
        """
        self.root_dir = Path(root_dir or os.getcwd()).resolve()
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.check_external = check_external
        self.use_gitignore = use_gitignore

        self.private_url_patterns: List[str] = []
        self.ignore_spec: Optional[pathspec.PathSpec] = None

    def load_config(self) -> None:
        """Load configuration from config file."""
        config_path = self.root_dir / self.config_file

        if not config_path.exists():
            return

        # Simple config parser (avoid adding yaml dependency)
        # Format: one private URL pattern per line
        # Lines starting with # are comments
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Support YAML-like format: "- pattern" or just "pattern"
                    if line.startswith("- "):
                        line = line[2:].strip()
                    # Skip YAML keys (lines ending with : that are not URLs)
                    if line and not (
                        line.endswith(":") and not line.startswith(("http://", "https://"))
                    ):
                        self.private_url_patterns.append(line)

    def load_gitignore(self) -> None:
        """Load .gitignore patterns."""
        if not self.use_gitignore:
            return

        gitignore_path = self.root_dir / self.DEFAULT_IGNORE_FILE
        if not gitignore_path.exists():
            return

        with open(gitignore_path) as f:
            patterns = [
                line.strip() for line in f if line.strip() and not line.strip().startswith("#")
            ]

        # Always ignore .git directory
        if ".git" not in patterns and ".git/" not in patterns:
            patterns.append(".git/")

        if patterns:
            self.ignore_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, patterns
            )

    def get_markdown_files(self) -> List[str]:
        """Get all markdown files in the repository.

        Returns:
            List of relative paths to markdown files.
        """
        markdown_files = []

        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.root_dir)

            # Filter directories based on ignore patterns
            if self.ignore_spec:
                dirs_to_remove = []
                for d in dirs:
                    dir_rel_path = str(rel_root / d)
                    check_path = dir_rel_path + "/"
                    if self.ignore_spec.match_file(check_path):
                        dirs_to_remove.append(d)

                for d in dirs_to_remove:
                    dirs.remove(d)

            # Add markdown files
            for file in files:
                if file.endswith((".md", ".markdown")):
                    file_rel_path = rel_root / file
                    file_rel_str = str(file_rel_path)

                    # Check if file is ignored
                    if self.ignore_spec and self.ignore_spec.match_file(file_rel_str):
                        continue

                    markdown_files.append(file_rel_str)

        return markdown_files

    def extract_links_from_file(self, file_path: str) -> List[Link]:
        """Extract all links from a markdown file.

        Args:
            file_path: Relative path to markdown file.

        Returns:
            List of Link objects found in the file.
        """
        full_path = self.root_dir / file_path
        links = []

        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            # Skip files that can't be read
            return links

        # Extract reference definitions first
        references: Dict[str, str] = {}
        for match in self.REFERENCE_DEF_PATTERN.finditer(content):
            ref_id = match.group(1).lower()
            url = match.group(2)
            references[ref_id] = url

        # Extract inline links: [text](url)
        for match in self.INLINE_LINK_PATTERN.finditer(content):
            text = match.group(1)
            url = match.group(2)

            # Find line number
            line_num = content[: match.start()].count("\n") + 1

            # Parse URL and anchor
            parsed_url, anchor = self._parse_url_and_anchor(url)

            link = Link(
                text=text,
                url=parsed_url,
                file_path=file_path,
                line_number=line_num,
                anchor=anchor,
            )

            self._classify_link(link)
            links.append(link)

        # Extract reference-style links: [text][ref]
        # This is more complex and can have false positives, so we skip for now
        # to keep the implementation simple. Can be added later if needed.

        return links

    def _parse_url_and_anchor(self, url: str) -> Tuple[str, Optional[str]]:
        """Parse URL and extract anchor fragment.

        Args:
            url: URL string that may contain an anchor.

        Returns:
            Tuple of (url_without_anchor, anchor_or_none)
        """
        if "#" in url:
            parts = url.split("#", 1)
            return parts[0], parts[1]
        return url, None

    def _classify_link(self, link: Link) -> None:
        """Classify link as external/internal and check if private.

        Modifies link in place to set is_external and is_private flags.

        Args:
            link: Link object to classify.
        """
        url = link.url

        # Check if it's an external URL
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme in ("http", "https", "ftp"):
            link.is_external = True

            # Check if it matches a private pattern
            for pattern in self.private_url_patterns:
                if self._matches_private_pattern(url, pattern):
                    link.is_private = True
                    break
        else:
            link.is_external = False

    def _matches_private_pattern(self, url: str, pattern: str) -> bool:
        """Check if URL matches a private URL pattern.

        Args:
            url: URL to check.
            pattern: Pattern to match (domain or prefix).

        Returns:
            True if URL matches pattern.
        """
        # Pattern can be:
        # 1. Domain: "internal.company.com"
        # 2. Prefix: "https://internal.company.com/"
        # 3. Prefix with port: "http://localhost:"

        if pattern.startswith(("http://", "https://")):
            # Prefix match
            return url.startswith(pattern)
        else:
            # Domain match - check if domain is in URL
            parsed = urllib.parse.urlparse(url)
            return pattern in parsed.netloc

    def validate_internal_link(self, link: Link) -> Tuple[bool, str]:
        """Validate an internal (relative path) link.

        Args:
            link: Link object to validate.

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        # Handle anchor-only links
        if not link.url or link.url == "":
            if link.anchor:
                # Anchor-only link (#heading) - check in current file
                return self._validate_anchor(link.file_path, link.anchor)
            else:
                return False, "Empty link"

        # Get the directory containing the source file (relative to root)
        source_dir = self.root_dir / Path(link.file_path).parent

        # Resolve the target path relative to source file
        target_path = (source_dir / link.url).resolve()

        # Check if target is within root_dir (security check)
        try:
            target_path.relative_to(self.root_dir)
        except ValueError:
            return False, "Link points outside repository"

        # Check if target exists
        if not target_path.exists():
            return False, "File not found"

        # If there's an anchor, validate it in the target file
        if link.anchor:
            target_rel = str(target_path.relative_to(self.root_dir))
            return self._validate_anchor(target_rel, link.anchor)

        return True, ""

    def _validate_anchor(self, file_path: str, anchor: str) -> Tuple[bool, str]:
        """Validate that an anchor exists in a markdown file.

        Args:
            file_path: Relative path to markdown file.
            anchor: Anchor ID to find.

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        full_path = self.root_dir / file_path

        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return False, "Cannot read target file"

        # Extract headings and convert to anchor IDs
        heading_pattern = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
        for match in heading_pattern.finditer(content):
            heading_text = match.group(1).strip()
            heading_id = self._heading_to_anchor(heading_text)

            if heading_id == anchor:
                return True, ""

        return False, f"Anchor #{anchor} not found"

    def _heading_to_anchor(self, heading: str) -> str:
        """Convert markdown heading text to anchor ID.

        Follows GitHub-flavored markdown rules:
        - Convert to lowercase
        - Replace spaces with hyphens
        - Remove special characters

        Args:
            heading: Heading text.

        Returns:
            Anchor ID.
        """
        # Remove markdown formatting (bold, italic, code, links)
        heading = re.sub(r"\*+([^*]+)\*+", r"\1", heading)  # bold/italic
        heading = re.sub(r"`([^`]+)`", r"\1", heading)  # code
        heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)  # links

        # Convert to lowercase
        heading = heading.lower()

        # Replace spaces and special chars with hyphens
        heading = re.sub(r"[^\w\s-]", "", heading)
        heading = re.sub(r"[\s]+", "-", heading)

        return heading

    def validate_external_link(self, link: Link, retries: int = 2) -> Tuple[bool, str]:
        """Validate an external URL.

        Args:
            link: Link object to validate.
            retries: Number of retries on failure.

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        for attempt in range(retries + 1):
            try:
                # Use HEAD request first (faster)
                req = urllib.request.Request(link.url, method="HEAD")
                req.add_header("User-Agent", "spec-tools-link-validator/0.1.0")

                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    if 200 <= response.status < 400:
                        return True, ""
                    else:
                        return False, f"HTTP {response.status}"

            except urllib.error.HTTPError as e:
                if attempt == retries:
                    return False, f"HTTP {e.code}"
            except urllib.error.URLError as e:
                if attempt == retries:
                    return False, f"Connection error: {e.reason}"
            except Exception as e:
                if attempt == retries:
                    return False, f"Error: {type(e).__name__}"

        return False, "Unknown error"

    def validate(self, verbose: bool = False) -> LinkValidationResult:
        """Run link validation and return results.

        Args:
            verbose: Whether to print verbose output.

        Returns:
            LinkValidationResult containing validation results.
        """
        # Load configuration
        self.load_config()
        self.load_gitignore()

        # Get all markdown files
        markdown_files = self.get_markdown_files()

        if verbose:
            print(f"Found {len(markdown_files)} markdown files")

        # Extract all links
        all_links: List[Link] = []
        for md_file in markdown_files:
            links = self.extract_links_from_file(md_file)
            all_links.extend(links)

        if verbose:
            print(f"Found {len(all_links)} links")

        # Validate links
        valid_count = 0
        invalid_count = 0
        private_count = 0
        invalid_details = []

        # Validate internal links
        internal_links = [link for link in all_links if not link.is_external]
        for link in internal_links:
            is_valid, reason = self.validate_internal_link(link)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                invalid_details.append(
                    {
                        "file": link.file_path,
                        "line": str(link.line_number),
                        "url": link.url + (f"#{link.anchor}" if link.anchor else ""),
                        "reason": reason,
                    }
                )

        # Validate external links (with concurrency)
        external_links = [link for link in all_links if link.is_external and not link.is_private]
        private_links = [link for link in all_links if link.is_private]
        private_count = len(private_links)

        if self.check_external and external_links:
            if verbose:
                print(f"Checking {len(external_links)} external URLs...")

            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                future_to_link = {
                    executor.submit(self.validate_external_link, link): link
                    for link in external_links
                }

                for future in as_completed(future_to_link):
                    link = future_to_link[future]
                    is_valid, reason = future.result()

                    if is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        invalid_details.append(
                            {
                                "file": link.file_path,
                                "line": str(link.line_number),
                                "url": link.url,
                                "reason": reason,
                            }
                        )
        elif not self.check_external:
            # External links are skipped
            pass

        total_links = len(all_links)

        return LinkValidationResult(
            total_links=total_links,
            valid_links=valid_count,
            invalid_links=invalid_count,
            private_links=private_count,
            skipped_links=len(external_links) if not self.check_external else 0,
            invalid_link_details=invalid_details,
            markdown_files_checked=len(markdown_files),
        )

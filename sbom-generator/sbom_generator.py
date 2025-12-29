#!/usr/bin/env python3

import argparse
import yaml
import sys
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from enum import Enum

from spdx_tools.spdx.model import (
    Actor,
    ActorType,
    CreationInfo,
    Document,
    Package,
    Relationship,
    RelationshipType,
    PackageVerificationCode,
    SpdxNoAssertion,
    File,
    ChecksumAlgorithm,
    Checksum,
)
from spdx_tools.common.spdx_licensing import spdx_licensing
from spdx_tools.spdx.writer.write_anything import write_file


class DistributionType(Enum):
    ARCHIVE = "archive"
    GIT_REPO = "repository"

    def __str__(self):
        return self.value


def convert_to_spdx_vcs_location(url):
    """Convert repository URL to SPDX VCS location format."""
    # Handle git repositories
    if url.endswith(".git"):
        if url.startswith("https://") or url.startswith("ssh://"):
            return f"git+{url}"
        elif url.startswith("git://"):
            return url  # Already in correct format
        else:
            return f"git+https://{url}"

    return url


def detect_file_metadata(file_path, patterns):
    """Detect metadata from file content using regex patterns."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        results = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            results[key] = (
                match.group(1)
                if match and match.groups()
                else (match.group(0) if match else SpdxNoAssertion())
            )

        return results

    except Exception:
        return {key: SpdxNoAssertion() for key in patterns.keys()}


def extract_manifest(directory):
    """Extract manifest information from repository."""
    manifest_path = directory / "manifest.yml"
    manifest_content = None
    dependencies = []

    required_keys_at_top_level = ["name", "version", "description", "license"]
    required_keys_per_dependency = ["name", "version", "license", "repository"]
    required_keys_per_dependency_repository = ["type", "url"]

    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_content = f.read()

        manifest = yaml.safe_load(manifest_content)

        if not all(key in manifest for key in required_keys_at_top_level):
            raise ValueError("manifest.yml is missing required keys at the top level")

        if "dependencies" in manifest:
            for dep in manifest["dependencies"]:
                if not all(key in dep for key in required_keys_per_dependency):
                    raise ValueError("A dependency is missing required keys")

                if not all(
                    key in dep["repository"]
                    for key in required_keys_per_dependency_repository
                ):
                    raise ValueError(
                        "A dependency's repository is missing required keys"
                    )

        if "testDependencies" in manifest:
            for dep in manifest["testDependencies"]:
                if not all(key in dep for key in required_keys_per_dependency):
                    raise ValueError("A dependency is missing required keys")

                if not all(
                    key in dep["repository"]
                    for key in required_keys_per_dependency_repository
                ):
                    raise ValueError(
                        "A dependency's repository is missing required keys"
                    )

        return manifest
    else:
        raise FileNotFoundError("manifest.yml not found in the given directory.")


def process_directory(directory, excluded_files=None):
    """Process directory and return manifest info and hashes."""
    directory = Path(directory)
    if excluded_files is None:
        excluded_files = []

    # Extract manifest
    manifest = extract_manifest(directory)

    excluded_file_list = []
    included_file_info = {}

    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = f"./{file_path.relative_to(directory)}"

            # Always ignore .git folders and .git files (including submodule .git files)
            if "/.git/" in relative_path or relative_path.endswith("/.git"):
                continue

            # Check if file should be excluded
            is_excluded = False
            for exc in excluded_files:
                exc_path = directory / exc.lstrip("./")
                if exc_path.is_dir():
                    # Directory exclusion - check if file is within directory
                    if (
                        relative_path.startswith(f"./{exc.lstrip('./')}/")
                        or relative_path == f"./{exc.lstrip('./')}"
                    ):
                        is_excluded = True
                        break
                else:
                    # File exclusion - exact match
                    if relative_path == exc:
                        is_excluded = True
                        break

            if is_excluded:
                excluded_file_list.append(relative_path)
            else:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                sha1_hash = hashlib.sha1(file_data).hexdigest()

                metadata = detect_file_metadata(
                    file_path,
                    {
                        "license": r"SPDX-License-Identifier:\s*([A-Za-z0-9\-\.+]+)",
                        "copyright": r"(Copyright\s+.*?All\s+Rights\s+Reserved\.?)",
                    },
                )
                included_file_info[relative_path] = {
                    "hash": sha1_hash,
                    "license": metadata["license"],
                    "copyright": metadata["copyright"],
                }

    return manifest, included_file_info, excluded_file_list


def generate_sbom(
    directory_path: Path,
    distribution_type: DistributionType,
    excluded_files=None,
    download_location=None,
    homepage=None,
    creator=None,
    document_namespace_prefix=None,
    include_file_hashes=False,
):
    """Generate SBOM from directory."""

    # Process directory to:
    #  -validate and retrieve the manifest of the directory
    #  -get file information (hash, license, copyright text) for all file's that are not excluded.
    #  -get the relative paths of each file (from directory) that was excluded (needed for PackageVerificationCode)
    manifest, included_file_info, excluded_file_list = process_directory(
        directory_path, excluded_files
    )

    # SBOM objects that will make up the SBOM document.

    creators = [
        Actor(ActorType.TOOL, "sbom-generator"),
        Actor(ActorType.ORGANIZATION, creator),
    ]
    creation_info = CreationInfo(
        spdx_version="SPDX-2.3",
        spdx_id="SPDXRef-DOCUMENT",
        name=f"",
        data_license="CC0-1.0",
        document_namespace="",
        creators=creators,
        created=datetime.now(),
    )
    packages = []
    relationships = []
    files = []

    # Generate output filenames based on package info
    output_files = [
        f"{manifest['name']}-{manifest['version']}-{str(distribution_type)}-SPDX2.3.spdx",
        f"{manifest['name']}-{manifest['version']}-{str(distribution_type)}-SPDX2.3.spdx.json",
        f"{manifest['name']}-{manifest['version']}-{str(distribution_type)}-SPDX2.3.spdx.xml",
        f"{manifest['name']}-{manifest['version']}-{str(distribution_type)}-SPDX2.3.spdx.yaml",
    ]

    # Calculate verification code for the main package

    # Always exclude SBOMs that will be included in the archive package.
    if distribution_type == DistributionType.ARCHIVE:
        excluded_file_list.extend([f"./{output_file}" for output_file in output_files])

    included_file_hashes = [info["hash"] for info in included_file_info.values()]
    included_file_hashes.sort()
    verification_string = "".join(included_file_hashes)
    verification_hash = hashlib.sha1(verification_string.encode()).hexdigest()

    verification_code = PackageVerificationCode(
        value=verification_hash, excluded_files=excluded_file_list
    )

    # Collect unique licenses from files and dependencies
    unique_licenses = set()
    
    # Add file licenses
    for file_info in included_file_info.values():
        file_license = file_info.get("license", SpdxNoAssertion())
        if not isinstance(file_license, SpdxNoAssertion) and file_license:
            unique_licenses.add(file_license)
    
    # Add dependency licenses (not test dependencies)
    if "dependencies" in manifest:
        for dep in manifest["dependencies"]:
            if not isinstance(dep["license"], SpdxNoAssertion) and dep["license"]:
                unique_licenses.add(dep["license"])
    
    # Create concluded license
    if unique_licenses:
        concluded_license = spdx_licensing.parse(" AND ".join(sorted(unique_licenses)))
    else:
        concluded_license = (
            manifest["license"]
            if isinstance(manifest["license"], SpdxNoAssertion)
            else spdx_licensing.parse(manifest["license"])
        )

    # Define the main software package of the given directory.
    source_info = None

    if distribution_type == DistributionType.GIT_REPO:
        source_info = "The package verification code was generated from the repository being cloned with --recurse-submodules."

    main_package = Package(
        name=manifest["name"],
        spdx_id="SPDXRef-Package",
        download_location=download_location,
        version=manifest["version"],
        description=manifest["description"],
        files_analyzed=True,
        verification_code=verification_code,
        license_concluded=concluded_license,
        license_declared=(
            manifest["license"]
            if isinstance(manifest["license"], SpdxNoAssertion)
            else spdx_licensing.parse(manifest["license"])
        ),
        homepage=homepage,
        source_info=source_info
    )

    packages.append(main_package)

    # The documents created by this script always have the SPDX Ref ID of
    # SPDXRef-DOCUMENT. The document ID should always have a DESCRIBES
    # relationship for the package contained in the directory.
    relationships = [
        Relationship("SPDXRef-DOCUMENT", RelationshipType.DESCRIBES, "SPDXRef-Package")
    ]

    # Create file objects for the document if directed by CLI.
    if include_file_hashes:
        file_counter = 1
        for file_path, file_info in included_file_info.items():
            file_hash = file_info["hash"]
            file_license = file_info.get("license", SpdxNoAssertion())
            file_copyright = file_info.get("copyright", SpdxNoAssertion())

            file_obj = File(
                name=file_path,
                spdx_id=f"SPDXRef-File-{file_counter}",
                checksums=[Checksum(ChecksumAlgorithm.SHA1, file_hash)],
                license_concluded=(
                    file_license
                    if isinstance(file_license, SpdxNoAssertion)
                    else spdx_licensing.parse(file_license)
                ),
                copyright_text=file_copyright,
            )
            files.append(file_obj)
            # Create CONTAINS relationship between main package and file
            relationships.append(
                Relationship(
                    "SPDXRef-Package",
                    RelationshipType.CONTAINS,
                    f"SPDXRef-File-{file_counter}",
                )
            )
            file_counter += 1

    # Create dependency packages and relationships. TODO - Cleanup and
    # make function for this.
    if "dependencies" in manifest:
        for dep in manifest["dependencies"]:
            dep_spdx_id = f"SPDXRef-Package-{dep['name']}"

            # Get download location from repository info
            dep_download_location = SpdxNoAssertion()
            if "repository" in dep and "url" in dep["repository"]:
                base_url = convert_to_spdx_vcs_location(dep["repository"]["url"])
                # Add version if available
                if dep["version"]:
                    dep_download_location = f"{base_url}@{dep['version']}"
                else:
                    dep_download_location = base_url

            # Check if dependency has a local path and exists with files
            local_path = None
            if "repository" in dep and "path" in dep["repository"]:
                local_path = dep["repository"]["path"]

            relationship_type = RelationshipType.DEPENDENCY_OF

            if local_path:
                full_path = directory_path / local_path.lstrip("./")
                if (
                    full_path.exists()
                    and full_path.is_dir()
                    and any(full_path.rglob("*"))
                ):
                    relationship_type = RelationshipType.CONTAINS

            dep_package = Package(
                name=dep["name"],
                spdx_id=dep_spdx_id,
                download_location=dep_download_location,
                version=dep["version"],
                files_analyzed=False,
                license_concluded=(
                    dep["license"]
                    if isinstance(dep["license"], SpdxNoAssertion)
                    else spdx_licensing.parse(dep["license"])
                ),
                license_declared=(
                    dep["license"]
                    if isinstance(dep["license"], SpdxNoAssertion)
                    else spdx_licensing.parse(dep["license"])
                ),
            )

            packages.append(dep_package)

            # Always create DEPENDENCY_OF relationship
            relationships.append(
                Relationship(
                    dep_spdx_id, RelationshipType.DEPENDENCY_OF, "SPDXRef-Package"
                )
            )

            # Add CONTAINS relationship if dependency is bundled locally
            if relationship_type == RelationshipType.CONTAINS:
                relationships.append(
                    Relationship(
                        "SPDXRef-Package", RelationshipType.CONTAINS, dep_spdx_id
                    )
                )

    # Create test dependency packages and relationships. TODO - Cleanup and
    # make function for this.
    if "testDependencies" in manifest:
        for dep in manifest["testDependencies"]:
            dep_spdx_id = f"SPDXRef-Package-{dep['name']}"

            # Get download location from repository info
            dep_download_location = SpdxNoAssertion()
            if "repository" in dep and "url" in dep["repository"]:
                base_url = convert_to_spdx_vcs_location(dep["repository"]["url"])
                # Add version if available
                if dep["version"]:
                    dep_download_location = f"{base_url}@{dep['version']}"
                else:
                    dep_download_location = base_url

            # Check if dependency has a local path and exists with files
            local_path = None
            if "repository" in dep and "path" in dep["repository"]:
                local_path = dep["repository"]["path"]

            relationship_type = RelationshipType.TEST_DEPENDENCY_OF

            if local_path:
                full_path = directory_path / local_path.lstrip("./")
                if (
                    full_path.exists()
                    and full_path.is_dir()
                    and any(full_path.rglob("*"))
                ):
                    relationship_type = RelationshipType.CONTAINS

            dep_package = Package(
                name=dep["name"],
                spdx_id=dep_spdx_id,
                download_location=dep_download_location,
                version=dep["version"],
                files_analyzed=False,
                license_concluded=(
                    dep["license"]
                    if isinstance(dep["license"], SpdxNoAssertion)
                    else spdx_licensing.parse(dep["license"])
                ),
                license_declared=(
                    dep["license"]
                    if isinstance(dep["license"], SpdxNoAssertion)
                    else spdx_licensing.parse(dep["license"])
                ),
            )

            packages.append(dep_package)

            # Always create DEPENDENCY_OF relationship
            relationships.append(
                Relationship(
                    dep_spdx_id, RelationshipType.TEST_DEPENDENCY_OF, "SPDXRef-Package"
                )
            )

            # Add CONTAINS relationship if dependency is bundled locally
            if relationship_type == RelationshipType.CONTAINS:
                relationships.append(
                    Relationship(
                        "SPDXRef-Package", RelationshipType.CONTAINS, dep_spdx_id
                    )
                )

    # Write SBOM in all formats with unique namespaces
    for output_path in output_files:
        # Set document namespace using prefix + filename
        creation_info.name = (
            f"{manifest['name']} {manifest['version']} {str(distribution_type)} SBOM"
        )
        creation_info.document_namespace = (
            f"{document_namespace_prefix.rstrip('/')}/{output_path}"
        )

        document = Document(
            creation_info=creation_info,
            packages=packages,
            files=files,
            relationships=relationships,
        )

        write_file(document, output_path, validate=True)
        print(f"SPDX v2 SBOM generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SBOM from directory in all formats"
    )
    parser.add_argument(
        "directory", type=Path, help="Path to directory containing manifest.yml"
    )
    parser.add_argument(
        "-t",
        "--distribution-type",
        required=True,
        type=DistributionType,
        choices=list(DistributionType),
        help="Distribution method of package.",
    )
    parser.add_argument(
        "-c", "--creator", required=True, help="Creator organization name"
    )
    parser.add_argument(
        "-f",
        "--include-file-hashes",
        action="store_true",
        help="Include individual file information with hashes",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="append",
        help="Exclude files/directories from verification code (can be used multiple times)",
    )
    parser.add_argument(
        "-d", "--download-location", required=True, help="Package download location URL"
    )
    parser.add_argument("-p", "--homepage", required=True, help="Package homepage URL")
    parser.add_argument(
        "-n", "--namespace-prefix", required=True, help="Document namespace prefix URI"
    )

    args = parser.parse_args()
    generate_sbom(
        args.directory,
        args.distribution_type,
        args.exclude,
        args.download_location,
        args.homepage,
        args.creator,
        args.namespace_prefix,
        args.include_file_hashes,
    )


if __name__ == "__main__":
    main()

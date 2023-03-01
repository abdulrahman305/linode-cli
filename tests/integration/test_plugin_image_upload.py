import json
import os
import subprocess
import tempfile
from typing import List

import pytest
from helpers import get_random_text

REGION = "us-southeast"
BASE_CMD = ["linode-cli", "image-upload", "--region", REGION]

TEST_IMAGE_CONTENT = bytes(
    [
        0x1F,
        0x8B,
        0x08,
        0x08,
        0xBD,
        0x5C,
        0x91,
        0x60,
        0x00,
        0x03,
        0x74,
        0x65,
        0x73,
        0x74,
        0x2E,
        0x69,
        0x6D,
        0x67,
        0x00,
        0x03,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    ]
)


@pytest.fixture(scope="session", autouse=True)
def fake_image_file():
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        fp.write(TEST_IMAGE_CONTENT)
        file_path = fp.name

    yield file_path

    os.remove(file_path)


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
    )
    return process


def test_help():
    process = exec_test_command(BASE_CMD + ["--help"])
    output = process.stdout.decode()

    assert process.returncode == 0
    assert "positional arguments" in output
    assert "optional arguments" in output


def test_invalid_file(
    fake_image_file,
):
    file_path = fake_image_file + "_fake"
    process = exec_test_command(
        BASE_CMD + ["--label", "notimportant", file_path]
    )
    output = process.stdout.decode()

    assert process.returncode == 2
    assert f"No file at {file_path}" in output


def test_file_upload(
    fake_image_file,
):
    file_path = fake_image_file
    label = f"cli-test-{get_random_text()}"
    description = "test description"

    # Upload the test image
    process = exec_test_command(
        BASE_CMD + ["--label", label, "--description", description, file_path]
    )

    output = process.stdout.decode()

    assert process.returncode == 0
    assert label in output
    assert description in output
    assert "pending_upload" in output

    # Get the new image from the API
    process = exec_test_command(
        ["linode-cli", "images", "ls", "--json", "--label", label]
    )
    assert process.returncode == 0

    image = json.loads(process.stdout.decode())

    assert image[0]["label"] in output

    # Delete the image
    process = exec_test_command(["linode-cli", "images", "rm", image[0]["id"]])
    assert process.returncode == 0

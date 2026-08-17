"""Behavioral coverage for Academy build-time context and validation."""

from pathlib import Path
import json
import shutil
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from devyco.academy import academy_course_context, load_academy_context  # noqa: E402


FIXTURES = Path(__file__).parent / "fixtures" / "academy"


def mutable_academy(tmp_path):
    target = tmp_path / "Academy"
    shutil.copytree(FIXTURES / "valid" / "Academy", target)
    return target


def write_root(academy_dir, update):
    filename = academy_dir / ".conf.json"
    config = json.loads(filename.read_text())
    update(config)
    filename.write_text(json.dumps(config))


def write_child(academy_dir, slug, update):
    filename = academy_dir / slug / ".conf.json"
    config = json.loads(filename.read_text())
    update(config["vars"][0]["values"])
    filename.write_text(json.dumps(config))


def test_ordered_configuration_produces_normalized_academy_context():
    context = load_academy_context(str(FIXTURES / "valid" / "Academy"))

    assert [item["slug"] for item in context["academy_order"]] == [
        "live-course",
        "soon-course",
    ]
    assert context["academy_order"][0] == {
        "slug": "live-course",
        "title": "Build a Live Course",
        "status": "live",
        "is_hidden": False,
        "duration": "~2 hrs",
        "description": "Replace an unsafe workflow with a tested hardware-backed result.",
        "prerequisite": "Comfortable with web development. No prior hardware experience needed.",
        "tags": ["WebAuthn"],
        "roles": ["app-builder"],
        "availability": None,
        "url": "/Academy/live-course/",
        "youtube_id": None,
    }
    assert context["academy_order"][1]["status"] == "coming-soon"
    assert context["academy_order"][1]["is_hidden"] is True
    assert context["academy_order"][1]["availability"] == "Coming Q4 2026"
    assert context["active_tags"] == ["WebAuthn", "FIPS"]
    assert context["where_to_start"] == [
        {
            "prompt": "Starting with a live course?",
            "slug": "live-course",
            "title": "Build a Live Course",
            "status": "live",
            "url": "/Academy/live-course/",
        },
        {
            "prompt": "Waiting for the next course?",
            "slug": "soon-course",
            "title": "Prepare a Coming Soon Course",
            "status": "coming-soon",
            "url": "/Academy/soon-course/",
        },
    ]


def test_duplicate_order_slug_fails_with_config_path(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    write_root(
        academy_dir,
        lambda config: config["order"].append("live-course"),
    )

    with pytest.raises(ValueError, match=r"\.conf\.json.*duplicate.*live-course"):
        load_academy_context(str(academy_dir))


def test_hidden_slug_outside_order_fails_with_config_path(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    write_root(
        academy_dir,
        lambda config: config["hidden"].append("orphan-course"),
    )

    with pytest.raises(
        ValueError,
        match=r"\.conf\.json.*hidden.*orphan-course.*order",
    ):
        load_academy_context(str(academy_dir))


def test_missing_ordered_child_directory_fails_with_path(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    write_root(
        academy_dir,
        lambda config: config["order"].append("missing-course"),
    )

    with pytest.raises(ValueError, match=r"Academy/missing-course.*directory"):
        load_academy_context(str(academy_dir))


def test_missing_child_config_fails_with_path(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    (academy_dir / "soon-course" / ".conf.json").unlink()

    with pytest.raises(ValueError, match=r"soon-course/\.conf\.json.*missing"):
        load_academy_context(str(academy_dir))


def test_missing_child_content_fails_with_path(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    (academy_dir / "soon-course" / "index.adoc").unlink()

    with pytest.raises(ValueError, match=r"soon-course/index\.adoc.*missing"):
        load_academy_context(str(academy_dir))


@pytest.mark.parametrize(
    "slug,update,message",
    [
        (
            "live-course",
            lambda values: values.update({"status": "live"}),
            r"live-course/\.conf\.json.*status.*remove",
        ),
        (
            "live-course",
            lambda values: values.pop("description"),
            r"live-course/\.conf\.json.*description.*required",
        ),
        (
            "live-course",
            lambda values: values.update({"tags": ["NotATag"]}),
            r"live-course/\.conf\.json.*tag.*NotATag",
        ),
        (
            "soon-course",
            lambda values: values.pop("availability"),
            r"soon-course/\.conf\.json.*availability.*required",
        ),
        (
            "live-course",
            lambda values: values.pop("duration"),
            r"live-course/\.conf\.json.*duration.*required",
        ),
        (
            "live-course",
            lambda values: values.update({"duration": "2 hours"}),
            r"live-course/\.conf\.json.*duration.*2 hours",
        ),
    ],
)
def test_invalid_child_metadata_fails_with_path(
    tmp_path,
    slug,
    update,
    message,
):
    academy_dir = mutable_academy(tmp_path)
    write_child(academy_dir, slug, update)

    with pytest.raises(ValueError, match=message):
        load_academy_context(str(academy_dir))


@pytest.mark.parametrize(
    "update,message",
    [
        (
            lambda config: config["where_to_start"].append(
                {"prompt": "Broken target?", "slug": "missing-course"},
            ),
            r"\.conf\.json.*where_to_start.*missing-course.*order",
        ),
        (
            lambda config: config["where_to_start"].append(
                {
                    "prompt": config["where_to_start"][0]["prompt"],
                    "slug": "soon-course",
                },
            ),
            r"\.conf\.json.*where_to_start.*duplicate.*Starting with a live course",
        ),
    ],
)
def test_invalid_guidance_fails_with_root_config_path(tmp_path, update, message):
    academy_dir = mutable_academy(tmp_path)
    write_root(academy_dir, update)

    with pytest.raises(ValueError, match=message):
        load_academy_context(str(academy_dir))


def test_course_context_derives_stub_navigation_metadata_and_analytics():
    academy = load_academy_context(str(FIXTURES / "valid" / "Academy"))

    live = academy_course_context(academy, "live-course")
    assert live["current_index"] == 0
    assert live["current_tutorial"]["slug"] == "live-course"
    assert live["is_stub"] is False
    assert live["prev_tutorial"] is None
    assert live["next_tutorial"] is None
    assert live["canonical_url"] == (
        "https://developers.yubico.com/Academy/live-course/"
    )
    assert live["og_title"] == "Build a Live Course"
    assert live["og_description"].startswith("Replace an unsafe workflow")
    assert live["og_image_url"] == (
        "https://developers.yubico.com/img/academy-social.png"
    )
    assert live["og_safe"] is True
    assert live["analytics_tutorial_name"] == "Build a Live Course"
    assert live["analytics_tutorial_slug"] == "live-course"

    stub = academy_course_context(academy, "soon-course")
    assert stub["is_stub"] is True
    assert stub["sidebar_entries"] is academy["academy_order"]
    assert stub["prev_tutorial"]["slug"] == "live-course"
    assert stub["next_tutorial"] is None

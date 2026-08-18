"""Behavioral coverage for Academy build-time context and validation."""

from pathlib import Path
import json
import re
import shutil
import sys

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from devyco.academy import academy_course_context, load_academy_context  # noqa: E402


FIXTURES = Path(__file__).parent / "fixtures" / "academy"


def test_mobile_academy_breadcrumb_does_not_inherit_ordered_list_margin():
    academy_css = (REPO_ROOT / "static" / "css" / "academy.css").read_text()

    assert ".academy-course-page .breadcrumb { margin-left: 0; }" in academy_css
    assert ".academy-course-content p a," in academy_css
    assert "text-decoration: underline;" in academy_css


def test_share_links_keep_contrasting_text_on_hover():
    academy_css = (REPO_ROOT / "static" / "css" / "academy.css").read_text()

    hover_rule = re.search(
        r"\.academy-course-page \.academy-share-controls a:hover[^\{]*\{([^}]*)\}",
        academy_css,
    )

    assert hover_rule is not None
    declarations = hover_rule.group(1)
    assert "background: var(--academy-teal);" in declarations
    assert "color: #fff;" in declarations


def test_academy_shared_markup_and_content_include_accessibility_semantics():
    boilerplate = (REPO_ROOT / "templates" / "boilerplate.template").read_text()
    cookie_config = (REPO_ROOT / "static" / "js" / "cookieconsent-init.js").read_text()
    passkey_content = (
        REPO_ROOT / "content" / "Academy" / "passkey-app" / "index.adoc"
    ).read_text()

    assert '<html lang="en" class="no-js' in boilerplate
    assert 'consent_modal: {\n        title: "Cookie preferences",' in cookie_config
    assert '[cols="2,4,4", options="header"]' in passkey_content


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


def render_hub(academy_dir):
    context = load_academy_context(str(academy_dir))
    context.update({"content": "", "nav": [], "title": "Developer Academy"})
    environment = Environment(loader=FileSystemLoader(str(REPO_ROOT / "templates")))
    return BeautifulSoup(
        environment.get_template("academy.template").render(**context),
        "html.parser",
    )


def render_course(academy_dir, slug, content=""):
    academy = load_academy_context(str(academy_dir))
    context = academy_course_context(academy, slug)
    context.update(academy)
    context.update(context["current_tutorial"])
    context.update({"content": content, "nav": [], "title": context["current_tutorial"]["title"]})
    environment = Environment(loader=FileSystemLoader(str(REPO_ROOT / "templates")))
    return BeautifulSoup(
        environment.get_template("academy-course.template").render(**context),
        "html.parser",
    )


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


def test_hub_renders_cards_filters_and_guidance_from_configuration():
    page = render_hub(FIXTURES / "valid" / "Academy")

    cards = page.select("[data-academy-card]")
    assert [card["data-tutorial-slug"] for card in cards] == [
        "live-course",
        "soon-course",
    ]
    assert cards[0].select_one(".academy-card-title").get_text(strip=True) == (
        "Build a Live Course"
    )
    assert cards[0].select_one(".academy-card-status").get_text(strip=True) == "Live"
    assert cards[0].select_one(".academy-card-timing").get_text(strip=True) == "~2 hrs"
    assert cards[0].select_one(".academy-card-prerequisite").get_text(" ", strip=True).startswith(
        "Before you start: Comfortable with web development"
    )
    assert cards[1].select_one(".academy-card-status").get_text(strip=True) == (
        "Coming Soon"
    )
    assert cards[1].select_one(".academy-card-timing").get_text(strip=True) == (
        "Coming Q4 2026"
    )
    assert cards[1].select_one(".academy-card-notify")["href"].startswith(
        "https://www.yubico.com/newsletter/"
    )

    assert [button.get_text(strip=True) for button in page.select("[data-academy-filter]")] == [
        "All",
        "WebAuthn",
        "FIPS",
    ]
    assert [item["data-tutorial-slug"] for item in page.select(".academy-start-item")] == [
        "live-course",
        "soon-course",
    ]
    assert page.select_one(".academy-hero-cta")["href"] == "/Academy/live-course/"


def test_adding_ordered_configuration_adds_hub_card_and_filter(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    new_course = academy_dir / "ssh-course"
    shutil.copytree(academy_dir / "live-course", new_course)
    write_child(
        academy_dir,
        "ssh-course",
        lambda values: values.update(
            {
                "title": "Secure an SSH Workflow",
                "tags": ["SSH"],
            }
        ),
    )
    write_root(academy_dir, lambda config: config["order"].append("ssh-course"))

    page = render_hub(academy_dir)

    assert [card["data-tutorial-slug"] for card in page.select("[data-academy-card]")] == [
        "live-course",
        "soon-course",
        "ssh-course",
    ]
    assert [button.get_text(strip=True) for button in page.select("[data-academy-filter]")] == [
        "All",
        "WebAuthn",
        "FIPS",
        "SSH",
    ]


def test_coming_soon_page_suppresses_body_and_renders_preview_metadata():
    page = render_course(
        FIXTURES / "valid" / "Academy",
        "soon-course",
        '<h2>UNPUBLISHED BODY MARKER</h2><p>Secret implementation details.</p>',
    )

    assert "UNPUBLISHED BODY MARKER" not in page.get_text()
    stub = page.select_one("[data-academy-stub]")
    assert stub is not None
    assert page.select_one("h1").get_text(strip=True) == "Prepare a Coming Soon Course"
    assert page.select_one(".academy-stub-description").get_text(strip=True).startswith(
        "Plan a compliance workflow"
    )
    assert page.select_one(".academy-stub-prerequisite").get_text(" ", strip=True).startswith(
        "Before you start: Comfortable with PKI concepts"
    )
    assert page.select_one(".academy-stub-availability").get_text(strip=True) == (
        "Coming Q4 2026"
    )
    assert [tag.get_text(strip=True) for tag in page.select(".academy-stub-tags li")] == [
        "FIPS"
    ]
    assert page.select_one(".academy-stub-notify")["href"].startswith(
        "https://www.yubico.com/newsletter/"
    )
    assert [link["href"] for link in page.select(".academy-live-cross-sell a")] == [
        "/Academy/live-course/"
    ]


def test_live_page_renders_sidebar_and_live_only_adjacency(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    write_child(
        academy_dir,
        "soon-course",
        lambda values: values.update({"duration": "~3 hrs"}),
    )
    write_root(academy_dir, lambda config: config.update({"hidden": []}))

    page = render_course(
        academy_dir,
        "soon-course",
        '<h2 id="first-step">First step</h2><p>Published tutorial content.</p>',
    )

    assert [item["data-tutorial-slug"] for item in page.select(".academy-class-item")] == [
        "live-course",
        "soon-course",
    ]
    current = page.select_one('.academy-class-item[aria-current="page"]')
    assert current["data-tutorial-slug"] == "soon-course"
    assert page.select_one(".academy-prev-next .academy-previous")["href"] == (
        "/Academy/live-course/"
    )
    assert page.select_one(".academy-prev-next .academy-next") is None


def test_reorder_and_launch_transitions_update_every_rendered_surface(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    write_child(
        academy_dir,
        "soon-course",
        lambda values: values.update({"duration": "~3 hrs"}),
    )
    write_root(
        academy_dir,
        lambda config: config.update(
            {
                "order": ["soon-course", "live-course"],
                "hidden": [],
            }
        ),
    )

    hub = render_hub(academy_dir)
    cards = hub.select("[data-academy-card]")
    assert [card["data-tutorial-slug"] for card in cards] == [
        "soon-course",
        "live-course",
    ]
    assert cards[0].select_one(".academy-card-status").get_text(strip=True) == "Live"
    assert cards[0].select_one(".academy-card-timing").get_text(strip=True) == "~3 hrs"
    assert cards[0].select_one("[data-academy-notify]") is None

    course = render_course(academy_dir, "soon-course", '<h2 id="published">Published</h2>')
    assert course.select_one("[data-academy-page-status='live']") is not None
    assert [item["data-tutorial-slug"] for item in course.select(".academy-class-item")] == [
        "soon-course",
        "live-course",
    ]
    assert course.select_one(".academy-next")["href"] == "/Academy/live-course/"


@pytest.mark.parametrize("slug", ["live-course", "soon-course"])
def test_course_renders_safe_canonical_and_open_graph_metadata(slug):
    page = render_course(
        FIXTURES / "valid" / "Academy",
        slug,
        '<p>UNPUBLISHED META MARKER</p>',
    )
    academy = load_academy_context(str(FIXTURES / "valid" / "Academy"))
    tutorial = next(item for item in academy["academy_order"] if item["slug"] == slug)

    assert page.select_one('link[rel="canonical"]')["href"] == (
        "https://developers.yubico.com%s" % tutorial["url"]
    )
    assert page.select_one('meta[property="og:title"]')["content"] == tutorial["title"]
    assert page.select_one('meta[property="og:description"]')["content"] == tutorial["description"]
    assert page.select_one('meta[property="og:image"]')["content"] == (
        "https://developers.yubico.com/img/academy-social.png"
    )
    assert page.select_one('meta[property="og:url"]')["content"].endswith(tutorial["url"])
    assert page.select_one('meta[name="twitter:card"]')["content"] == "summary_large_image"
    assert "UNPUBLISHED META MARKER" not in str(page.head)


def test_live_course_renders_share_controls_and_newsletter_cta():
    page = render_course(FIXTURES / "valid" / "Academy", "live-course", "<h2>FAQ</h2>")

    share = page.select_one(".academy-share-row")
    assert share is not None
    assert [control.get_text(" ", strip=True) for control in share.select("[data-academy-share]")] == [
        "Twitter/X",
        "LinkedIn",
        "Bluesky",
        "Copy Link",
    ]
    for control in share.select("[data-academy-share]"):
        assert control.get("aria-label")
    for control in share.select('a[data-academy-share]'):
        assert "utm_source%3Dacademy-share" in control["href"]
        assert "utm_medium%3Dsocial" in control["href"]
        assert "utm_campaign%3Dlive-course" in control["href"]
    copy_link = share.select_one('[data-academy-share="copy-link"]')
    assert copy_link["data-academy-copy-link"].endswith(
        "?utm_source=academy-share&utm_medium=social&utm_campaign=live-course"
    )
    assert share.select_one('[role="status"][aria-live="polite"]') is not None
    assert page.select_one("[data-academy-native-share]") is not None
    assert page.select_one(".academy-newsletter-cta")["href"].startswith(
        "https://www.yubico.com/newsletter/"
    )


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

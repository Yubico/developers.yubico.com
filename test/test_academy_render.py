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
GLOBAL_NAV = [
    {"active": False, "hidden": False, "name": "Passkeys", "url": "/Passkeys/"},
    {"active": True, "hidden": False, "name": "Academy", "url": "/Academy/"},
    {"active": False, "hidden": True, "name": "Hidden", "url": "/Hidden/"},
]


def test_global_navigation_configuration_follows_product_and_traffic_priority():
    config = json.loads((REPO_ROOT / "content" / ".conf.json").read_text())

    assert config["order"] == [
        "Academy",
        "Passkeys",
        "SSH",
        "WebAuthn",
        "OTP",
        "PIV",
        "CTAP",
        "Secure_Domain",
        "Software_Projects",
        "YubiHSM2",
        "OATH",
        "PGP",
    ]
    assert "SSH" not in config["hidden"]


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
    context.update({"content": "", "nav": GLOBAL_NAV, "title": "Developer Academy"})
    environment = Environment(loader=FileSystemLoader(str(REPO_ROOT / "templates")))
    return BeautifulSoup(
        environment.get_template("academy.template").render(**context),
        "html.parser",
    )


def render_site(content="<p>Standard content marker</p>"):
    context = {
        "content": content,
        "current": None,
        "is_index": False,
        "nav": GLOBAL_NAV,
        "sidelinks": [],
        "title": "Standard page",
    }
    environment = Environment(loader=FileSystemLoader(str(REPO_ROOT / "templates")))
    return BeautifulSoup(
        environment.get_template("site.template").render(**context),
        "html.parser",
    )


def render_course(academy_dir, slug, content=""):
    academy = load_academy_context(str(academy_dir))
    context = academy_course_context(academy, slug)
    context.update(academy)
    context.update(context["current_tutorial"])
    context.update(
        {
            "content": content,
            "nav": GLOBAL_NAV,
            "title": context["current_tutorial"]["title"],
        }
    )
    environment = Environment(loader=FileSystemLoader(str(REPO_ROOT / "templates")))
    return BeautifulSoup(
        environment.get_template("academy-course.template").render(**context),
        "html.parser",
    )


def test_academy_pages_render_canonical_global_navigation():
    standard = render_site()
    hub = render_hub(FIXTURES / "valid" / "Academy")
    course = render_course(FIXTURES / "valid" / "Academy", "live-course")

    standard_nav = standard.select_one("nav.navbar-top")
    assert standard_nav is not None
    assert "navbar-expand-md" in standard_nav.get("class", [])
    assert standard_nav.has_attr("data-priority-nav")
    primary_links = standard_nav.select(
        "[data-priority-items] > li:not([data-priority-more]) > .nav-link"
    )
    assert [link.get_text(strip=True) for link in primary_links] == [
        "Passkeys",
        "Academy",
    ]
    assert standard_nav.select_one('.nav-link[aria-current="page"]')["href"] == "/Academy/"
    toggler = standard_nav.select_one(".navbar-toggler")
    assert toggler["aria-controls"] == "navbarToggler"
    assert toggler["data-bs-target"] == "#navbarToggler"
    collapse = standard_nav.select_one("#navbarToggler")
    assert collapse is not None
    assert collapse.select_one("[data-priority-items]") is not None
    more = collapse.select_one("[data-priority-more]")
    assert more is not None
    assert more.select_one("[data-priority-overflow]") is not None
    search = standard_nav.select_one("#search-box")
    assert search is not None
    assert search.find_parent(id="navbarToggler") is None
    assert search["role"] == "search"
    assert search["aria-label"] == "Site search"
    for page in (hub, course):
        navigation = page.select("nav.navbar-top")
        assert len(navigation) == 1
        assert navigation[0].decode() == standard_nav.decode()
        search = navigation[0].select_one("#search-box")
        assert search is not None
        loader = search.select_one('script[data-cookiecategory="functional"]')
        assert loader is not None
        assert "https://www.google.com/cse/cse.js?cx=" in loader.string


def test_academy_pages_render_canonical_global_footer():
    standard = render_site()
    hub = render_hub(FIXTURES / "valid" / "Academy")
    course = render_course(FIXTURES / "valid" / "Academy", "live-course")

    standard_footer = standard.select_one("footer")
    assert standard_footer is not None
    newsletter = standard_footer.find("a", string="Newsletter")
    assert newsletter["href"] == "https://www.yubico.com/email-subscription/"
    assert standard_footer.select_one('a[title="YouTube"]')["href"] == (
        "https://www.youtube.com/@YubicoDevelopers"
    )
    for page in (hub, course):
        footers = page.select("footer")
        assert len(footers) == 1
        assert footers[0].decode() == standard_footer.decode()


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
            "image": None,
            "image_alt": None,
            "image_url": None,
            "image_width": None,
            "image_height": None,
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
        "https://www.yubico.com/email-subscription/"
    )

    assert [button.get_text(strip=True) for button in page.select(".academy-filter-controls [data-academy-filter]")] == [
        "All",
        "WebAuthn",
        "FIPS",
    ]
    assert [button.get_text(strip=True) for button in cards[0].select(".academy-card-tag")] == [
        "WebAuthn"
    ]
    assert [item["data-tutorial-slug"] for item in page.select(".academy-start-item")] == [
        "live-course",
        "soon-course",
    ]
    assert page.select_one(".academy-hero-cta")["href"] == "/Academy/live-course/"

    community_links = {
        link.get_text(" ", strip=True): link["href"]
        for link in page.select(".academy-community a")
    }
    assert community_links["YubicoLabs on GitHub"] == "https://github.com/yubicolabs/"
    assert community_links["Yubico Developers on YouTube"] == (
        "https://www.youtube.com/@YubicoDevelopers"
    )


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
    assert [button.get_text(strip=True) for button in page.select(".academy-filter-controls [data-academy-filter]")] == [
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
        "https://www.yubico.com/email-subscription/"
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


def test_live_tutorial_artwork_maps_to_hub_hero_and_social_metadata():
    academy_dir = REPO_ROOT / "content" / "Academy"
    academy = load_academy_context(str(academy_dir))
    expected = {
        "passkey-app": "academy-passkey-app.png",
        "webauthn-deep-dive": "academy-webauthn-deep-dive.png",
        "securing-ssh": "academy-securing-ssh.png",
    }
    assert {item["slug"]: item["image"] for item in academy["academy_order"] if item["image"]} == expected

    hub = render_hub(academy_dir)
    for slug, filename in expected.items():
        card = hub.select_one('[data-tutorial-slug="%s"]' % slug)
        image = card.select_one("img.academy-card-image")
        image_link = image.find_parent("a")
        assert image["src"] == "/img/%s" % filename.replace(".png", ".webp")
        assert image["alt"]
        assert image["width"] == "1200"
        assert image["height"] == "670" or image["height"] == "634"
        assert image_link["href"] == "/Academy/%s/" % slug
        assert image_link["aria-label"] == "Open %s" % card.select_one(
            ".academy-card-title"
        ).get_text(strip=True)
        assert "academy-card-image-link" in image_link.get("class", [])

        page = render_course(academy_dir, slug, "<h2>Introduction</h2>")
        hero = page.select_one("img.academy-course-image")
        assert hero["src"] == image["src"]
        assert hero["alt"] == image["alt"]
        assert page.select_one('meta[property="og:image"]')["content"] == (
            "https://developers.yubico.com/img/%s" % filename
        )


def test_tutorial_without_artwork_uses_shared_social_fallback_and_no_empty_image():
    academy_dir = FIXTURES / "valid" / "Academy"
    hub = render_hub(academy_dir)
    page = render_course(academy_dir, "live-course", "<h2>Introduction</h2>")
    assert hub.select_one(".academy-card-image") is None
    assert page.select_one(".academy-course-image") is None
    assert page.select_one('meta[property="og:image"]')["content"] == (
        "https://developers.yubico.com/img/academy-social.png"
    )


def test_artwork_rejects_unsafe_paths_and_requires_alt_text(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    write_child(academy_dir, "live-course", lambda values: values.update({"image": "../secret.png", "image_alt": "Secret"}))
    with pytest.raises(ValueError, match=r"live-course/\.conf\.json.*image.*basename"):
        load_academy_context(str(academy_dir))

    write_child(academy_dir, "live-course", lambda values: values.update({"image": "missing.png", "image_alt": ""}))
    with pytest.raises(ValueError, match=r"live-course/\.conf\.json.*image_alt.*required"):
        load_academy_context(str(academy_dir))


def test_artwork_requires_a_png_basename(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    write_child(
        academy_dir,
        "live-course",
        lambda values: values.update({"image": "tutorial.jpg", "image_alt": "Tutorial artwork"}),
    )
    with pytest.raises(ValueError, match=r"live-course/\.conf\.json.*image.*PNG basename"):
        load_academy_context(str(academy_dir))


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
        "https://www.yubico.com/email-subscription/"
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


def test_live_sequence_renders_hub_return_only_for_the_last_tutorial(tmp_path):
    academy_dir = mutable_academy(tmp_path)
    shutil.copytree(academy_dir / "soon-course", academy_dir / "last-course")
    write_child(
        academy_dir,
        "soon-course",
        lambda values: values.update({"duration": "~3 hrs"}),
    )
    write_child(
        academy_dir,
        "last-course",
        lambda values: values.update({
            "title": "Finish the Academy Sequence",
            "duration": "~1 hrs",
        }),
    )
    for slug in ("soon-course", "last-course"):
        write_child(academy_dir, slug, lambda values: values.pop("availability", None))
    write_root(
        academy_dir,
        lambda config: config.update({
            "order": ["live-course", "soon-course", "last-course"],
            "hidden": [],
        }),
    )

    first = render_course(academy_dir, "live-course")
    middle = render_course(academy_dir, "soon-course")
    last = render_course(academy_dir, "last-course")

    assert first.select_one(".academy-previous") is None
    assert first.select_one(".academy-next") is not None
    assert first.select_one(".academy-hub-return") is None
    assert middle.select_one(".academy-previous") is not None
    assert middle.select_one(".academy-next") is not None
    assert middle.select_one(".academy-hub-return") is None
    assert last.select_one(".academy-previous") is not None
    assert last.select_one(".academy-next") is None
    assert last.select_one(".academy-hub-return")["href"] == "/Academy/"

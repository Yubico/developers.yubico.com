"""Build-time Academy configuration aggregation.

This module intentionally uses only the Python standard library and syntax
compatible with the site's Python 2 build image.
"""

import json
import os
import re
import struct


VALID_TAGS = set(['WebAuthn', 'SSH', 'PIV', 'HSM', 'AI', 'FIPS', 'Mobile',
                  'Linux'])
DURATION = re.compile(r'^~(?:\d+(?:\.\d+)?) (?:hrs|min)$')


def _read_json(filename):
    with open(filename, 'r') as infile:
        return json.load(infile)


def _child_values(academy_dir, slug):
    child_config = _read_json(os.path.join(academy_dir, slug, '.conf.json'))
    return child_config['vars'][0]['values']


def _project_root(academy_dir):
    parent = os.path.dirname(academy_dir)
    if os.path.basename(parent) == 'content':
        return os.path.dirname(parent)
    return parent


def _png_dimensions(filename):
    with open(filename, 'rb') as image_file:
        header = image_file.read(24)
    if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('%s: image must be a PNG' % filename)
    return struct.unpack('>II', header[16:24])


def _validate_child(filename, values, is_hidden, academy_dir):
    if 'status' in values:
        raise ValueError('%s: status is a legacy lifecycle field; remove it' %
                         filename)

    for field in ['title', 'description', 'prerequisite', 'tags']:
        if field not in values or not values[field]:
            raise ValueError('%s: %s is required' % (filename, field))

    for tag in values['tags']:
        if tag not in VALID_TAGS:
            raise ValueError('%s: invalid tag %s' % (filename, tag))

    if is_hidden and not values.get('availability'):
        raise ValueError('%s: availability is required for hidden tutorial' %
                         filename)

    if not is_hidden and not values.get('duration'):
        raise ValueError('%s: duration is required for Live tutorial' %
                         filename)

    duration = values.get('duration')
    if duration and not DURATION.match(duration):
        raise ValueError('%s: invalid duration %s' % (filename, duration))

    image = values.get('image')
    if image:
        if image != os.path.basename(image):
            raise ValueError('%s: image must be a basename' % filename)
        if not image.lower().endswith('.png'):
            raise ValueError('%s: image must be a PNG basename' % filename)
        if not values.get('image_alt'):
            raise ValueError('%s: image_alt is required with image' % filename)
        image_file = os.path.join(_project_root(academy_dir), 'static', 'img', image)
        if not os.path.isfile(image_file):
            raise ValueError('%s: image file is missing: %s' % (filename, image_file))
        width, height = _png_dimensions(image_file)
        if width < 1200 or height < 630:
            raise ValueError('%s: image must be at least 1200x630' % filename)
        display_file = os.path.join(
            os.path.dirname(image_file), image[:-4] + '.webp')
        if not os.path.isfile(display_file):
            raise ValueError('%s: optimized display image is missing: %s' %
                             (filename, display_file))


def load_academy_context(academy_dir):
    """Return normalized Academy context from an Academy content directory."""
    root_filename = os.path.join(academy_dir, '.conf.json')
    root = _read_json(root_filename)
    order = root.get('order', [])
    seen = set()
    for slug in order:
        if slug in seen:
            raise ValueError('%s: duplicate slug in order: %s' %
                             (root_filename, slug))
        seen.add(slug)
    hidden = set(root.get('hidden', []))
    for slug in hidden:
        if slug not in seen:
            raise ValueError('%s: hidden slug %s is not present in order' %
                             (root_filename, slug))
    academy_order = []

    for slug in order:
        child_dir = os.path.join(academy_dir, slug)
        if not os.path.isdir(child_dir):
            raise ValueError('%s: ordered tutorial directory is missing' %
                             child_dir)
        child_config = os.path.join(child_dir, '.conf.json')
        if not os.path.isfile(child_config):
            raise ValueError('%s: child configuration is missing' %
                             child_config)
        child_content = os.path.join(child_dir, 'index.adoc')
        if not os.path.isfile(child_content):
            raise ValueError('%s: tutorial content is missing' % child_content)
        values = _child_values(academy_dir, slug)
        is_hidden = slug in hidden
        _validate_child(child_config, values, is_hidden, academy_dir)
        image = values.get('image')
        display_image = image[:-4] + '.webp' if image else None
        display_height = None
        if image:
            image_file = os.path.join(_project_root(academy_dir), 'static', 'img', image)
            image_width, image_height = _png_dimensions(image_file)
            display_height = int(round(float(image_height) * 1200 / image_width))
        academy_order.append({
            'slug': slug,
            'title': values['title'],
            'status': 'coming-soon' if is_hidden else 'live',
            'is_hidden': is_hidden,
            'duration': values.get('duration'),
            'description': values['description'],
            'prerequisite': values['prerequisite'],
            'tags': values['tags'],
            'roles': values.get('roles', []),
            'availability': values.get('availability') if is_hidden else None,
            'url': '/Academy/%s/' % slug,
            'youtube_id': values.get('youtube_id'),
            'image': image,
            'image_alt': values.get('image_alt') if image else None,
            'image_url': '/img/%s' % display_image if display_image else None,
            'image_width': 1200 if image else None,
            'image_height': display_height,
        })

    by_slug = dict((item['slug'], item) for item in academy_order)
    where_to_start = []
    guidance_prompts = set()
    for guidance in root.get('where_to_start', []):
        guidance_slug = guidance.get('slug')
        prompt = guidance.get('prompt')
        if guidance_slug not in by_slug:
            raise ValueError('%s: where_to_start slug %s is not in order' %
                             (root_filename, guidance_slug))
        if prompt in guidance_prompts:
            raise ValueError('%s: where_to_start duplicate prompt: %s' %
                             (root_filename, prompt))
        guidance_prompts.add(prompt)
        tutorial = by_slug[guidance['slug']]
        where_to_start.append({
            'prompt': guidance['prompt'],
            'slug': tutorial['slug'],
            'title': tutorial['title'],
            'status': tutorial['status'],
            'url': tutorial['url'],
        })

    active_tags = []
    for tutorial in academy_order:
        for tag in tutorial['tags']:
            if tag not in active_tags:
                active_tags.append(tag)

    return {
        'academy_order': academy_order,
        'where_to_start': where_to_start,
        'active_tags': active_tags,
    }


def _navigation_item(tutorial):
    if tutorial is None:
        return None
    return {
        'slug': tutorial['slug'],
        'title': tutorial['title'],
        'url': tutorial['url'],
        'status': tutorial['status'],
    }


def academy_course_context(academy, current_slug):
    """Derive course-page context from normalized Academy context."""
    ordered = academy['academy_order']
    current_index = None
    for index, tutorial in enumerate(ordered):
        if tutorial['slug'] == current_slug:
            current_index = index
            break
    if current_index is None:
        raise ValueError('Academy tutorial is not in order: %s' % current_slug)

    current = ordered[current_index]
    previous_live = None
    next_live = None
    for tutorial in ordered[:current_index]:
        if tutorial['status'] == 'live':
            previous_live = tutorial
    for tutorial in ordered[current_index + 1:]:
        if tutorial['status'] == 'live':
            next_live = tutorial
            break

    return {
        'current_slug': current_slug,
        'current_index': current_index,
        'current_tutorial': current,
        'is_stub': current['is_hidden'],
        'sidebar_entries': ordered,
        'prev_tutorial': _navigation_item(previous_live),
        'next_tutorial': _navigation_item(next_live),
        'canonical_url': ('https://developers.yubico.com/Academy/%s/' %
                          current_slug),
        'og_title': current['title'],
        'og_description': current['description'],
        'image_url': current.get('image_url'),
        'image_alt': current.get('image_alt'),
        'image_width': current.get('image_width'),
        'image_height': current.get('image_height'),
        'og_image_url': ('https://developers.yubico.com/img/%s' %
                         (current.get('image') or 'academy-social.png')),
        'og_safe': True,
        'analytics_tutorial_name': current['title'],
        'analytics_tutorial_slug': current_slug,
    }

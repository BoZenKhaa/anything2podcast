import logging
import time
from argparse import ArgumentParser
from datetime import datetime, timedelta
from email.utils import formatdate
from pathlib import Path

import yaml
from mutagen.mp3 import MP3

# Subtitle can be 255 char max, so dont use longer descriptions.

CHANNEL = """<?xml version="1.0" encoding="utf-8"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:itunesu="http://www.itunesu.com/feed" version="2.0">
<channel>
<link>{website_link}</link>
<language>en-us</language>
<copyright>&#xA9;2013</copyright>
<webMaster>your@email.com</webMaster>
<managingEditor>your@email.com</managingEditor>
<image>
<url>{image_link}</url>
<title>Show logo</title>
<link>{website_link}</link>
</image>
<itunes:owner>
<itunes:name>Your Name</itunes:name>
<itunes:email>your@email.com</itunes:email>
</itunes:owner>
<itunes:category text="Arts">
<itunes:category text="Books" />
</itunes:category>
<itunes:keywords>Keyword</itunes:keywords>
<itunes:explicit>no</itunes:explicit>
<itunes:image href="{image_link}" />
<atom:link href="{feed_link}" rel="self" type="application/rss+xml" />
<pubDate>{pub_date}</pubDate>
<title>{title}</title>
<itunes:author>{author}</itunes:author>
<description>{description}</description>
<itunes:summary>{description}</itunes:summary>
<itunes:subtitle>{description}</itunes:subtitle>
<lastBuildDate>{pub_date}</lastBuildDate>
{items}
</channel>
</rss>"""

ITEM = """<item>
<title>{title}</title>
<description>{description}</description>
<itunes:summary>{description}</itunes:summary>
<itunes:subtitle>{description}</itunes:subtitle>
<itunesu:category itunesu:code="112" />
<enclosure url="{mp3filename}" type="audio/mpeg" length="{length}" />
<guid>{mp3filename}</guid>
<itunes:duration>{length}</itunes:duration>
<pubDate>{pub_date}</pubDate>
</item>"""


def get_image(media_folder: Path, podcast_http: str):
    try:
        images = []
        for filename in media_folder.glob('*'):
            if filename.suffix in ('.jpg', '.jpeg', '.png', '.gif'):
                images.append(filename.name)

        image_link = podcast_http + f"/{images[0]}"
        logging.info(f'Image found:{images[0]}')
    except Exception:
        image_link = ''
    return image_link


def generate_feed_items(media_folder, episode_description, podcast_http, strip_mp3_metadata):
    start_dt = datetime.now()
    # start_dt = start_dt - timedelta(days=365)
    episodes_xml_str = ""
    for i, mp3filename in enumerate(Path(media_folder).glob('*.mp3')):
        logging.info(f'Processing {mp3filename}')
        item_metadata = {}
        # statinfo = os.stat(str(mp3filename))
        # size = str(statinfo.st_size)
        audio = MP3(mp3filename)
        length = audio.info.length
        if strip_mp3_metadata:
            audio.delete()
            audio.save()
        # print(audio.info)

        item_metadata['length'] = str(int(length))
        item_metadata['mp3filename'] = podcast_http + f'/{mp3filename.name}'
        item_metadata['title'] = mp3filename.stem
        item_metadata['description'] = episode_description
        dt = start_dt - timedelta(days=i)
        item_metadata['pub_date'] = formatdate(time.mktime(dt.timetuple())) 

        episodes_xml_str += ITEM.format(**item_metadata)
    return episodes_xml_str


def generate_feed(podcast_http="http://server/podcast_folder",
                  media_folder="C:/some/folder/with/media",
                  podcast_description="Brief podcast description",
                  podcast_title="Title",
                  author="Author",
                  strip_mp3_metadata=True):
    episodes_xml_str = generate_feed_items(media_folder, podcast_description, podcast_http, strip_mp3_metadata)

    channel_metadata = {}
    image_link = get_image(Path(media_folder), podcast_http)

    channel_metadata['image_link'] = image_link
    channel_metadata['pub_date'] = formatdate()
    channel_metadata['feed_link'] = podcast_http + "/feed.xml"
    channel_metadata['website_link'] = podcast_http + "/index.html"
    channel_metadata['description'] = ''  # podcast_description
    channel_metadata['title'] = podcast_title
    channel_metadata['author'] = author
    channel_metadata['items'] = episodes_xml_str

    # print(channel_metadata)

    xml_str = CHANNEL.format(**channel_metadata)

    with open(Path(media_folder) / 'feed.xml', 'wt', encoding='utf-8') as f:
        f.write(xml_str)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="config_filepath", required=True,
                        help="yaml file with podcast configuration", metavar="CONFIG.yaml")
    parser.add_argument("-v", "--verbose", dest="verbose", required=False,
                        help="Turn on logging", action='store_true')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    config = yaml.safe_load(open(args.config_filepath, 'rt', encoding='utf-8'))
    # print(config)
    generate_feed(**config)
    logging.info('Done.')

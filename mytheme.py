import os
import re
import shutil
import random
import logging
import subprocess
from datetime import datetime

import colorz
import click
from click_option_group import optgroup
from i3ipc import Connection
from screeninfo import get_monitors
from PIL import Image

logging.basicConfig(format='%(module)-12s: %(levelname)-8s : %(message)s')
logger = logging.getLogger()


def set_logging(debug):
    if debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(logging.DEBUG)
        # logging.basicConfig(level=logging.DEBUG)
        logger.debug("Debugging enabled.")
    else:
        logger.setLevel(logging.INFO)
    pil_logger = logging.getLogger('PIL')
    pil_logger.setLevel(logging.INFO)


def get_monitor_size():
    width = max([monitor.width for monitor in get_monitors()])
    height = max([monitor.height for monitor in get_monitors()])
    return width, height


def is_image_oriented(img_width, img_height, orientation):
    if orientation == 'horizontal':
        if img_width / img_height >= 1:
            ret_val = True
        else:
            ret_val = False
    else:
        if img_width / img_height <= 1:
            ret_val = True
        else:
            ret_val = False
    return ret_val


def is_image_in_scale(img_width, img_height, screen_width, screen_height):
    logger.debug(f"{img_width: 5} - {screen_width}, {img_height} - {screen_height}")
    if img_width < screen_width or img_height < screen_height:
        return False
    return True


def backup_file(file):
    file_path, file_name = os.path.split(os.path.abspath(file))
    file_backup_path = os.path.join(file_path, 'backup')
    backup_time = datetime.now().isoformat(timespec="seconds").replace(':', '-')
    file_backup = os.path.join(
        file_backup_path,
        f"{file_name}_BACKUP_{backup_time}"
    )

    logger.debug(f"Backup file '{file_name}' from '{file_path}' to '{file_backup}'.")
    if not os.path.exists(file_backup_path):
        logger.debug(f"Backup path does not exist. Creating '{file_backup_path}'.")
        os.mkdir(file_backup_path)
    shutil.copy(file, file_backup)


def get_image(image_path, orientation, scale=False):
    img_types = ['png', 'jpeg', 'jpg']
    screen_size = get_monitor_size() if scale else ""

    if os.path.isdir(image_path):
        images_in_dir = []
        for file in os.listdir(image_path):
            if os.path.isfile(os.path.join(image_path, file)) and file.endswith(tuple(img_types)):
                logger.debug(f"Testing {file} for usable dimensions.")
                img_path = os.path.join(image_path, file)
                with Image.open(img_path) as image:
                    img_size = image.size
                    if is_image_oriented(*img_size, orientation):
                        if scale and not is_image_in_scale(*img_size, *screen_size):
                            logger.info(
                                f"Image size {img_size} is lower than screen size {screen_size}. "
                                "Ignoring image."
                            )
                            continue
                        images_in_dir.append(img_path)
                    else:
                        logger.info(f"Ignoring image {file} because it is oriented vertically.")
            else:
                logger.debug(f"{file} is not a file or does not end with one of {', '.join(img_types)}")

        logger.debug(f"Selecting one image from {images_in_dir}.")
        image_path = random.choice(images_in_dir)
    else:
        logger.info("Image supplied. Skipping scale/orientation checks!")
    return image_path


def set_colors(colors, colors_path):
    backup_file(colors_path)

    logger.debug(f"Read colors file {colors_path}.")
    with open(colors_path, 'r') as colors_file:
        lines = colors_file.readlines()

    COLOR_REGEX = re.compile(r"^#define color(?P<color_num>\d\d?) (?P<color>.*$)")
    new_lines = []
    for line in lines:
        color_match = COLOR_REGEX.match(line)
        if color_match:
            color_num = int(color_match.group('color_num'))
            color_old = color_match.group('color')
            if color_num <= 7:
                color_new = colorz.hexify(colors[color_num][0])
            else:
                color_new = colorz.hexify(colors[color_num - 8][1])
            logger.debug(f"Replacing color{color_num} {color_old} with {color_new}.")
            line = line.replace(color_old, color_new)
        new_lines.append(line)

    with open(colors_path, 'w') as colors_file:
        colors_file.writelines(new_lines)
    logger.info("Successfully written new colors to colors-file.")


def format_rofi_color_line(line):
    line = line.strip()
    line = line.replace('color-normal', '').replace('color-active', '')
    line = line.replace('color-urgent', '').replace('color-window', '')
    line = line.replace(': "', '').replace('";', '').replace('#', '')
    return line


def set_rofi_colors(colors, rofi_path):
    backup_file(rofi_path)

    logger.debug(f"Read rofi file {rofi_path}.")
    with open(rofi_path, 'r') as rofi_file:
        lines = rofi_file.readlines()

    new_lines = []
    new_color = colorz.hexify(colors[random.randint(0, len(colors)-1)][0]).replace('#', '')
    logger.debug(f"Using random color for rofi: #{new_color}.")
    for line in lines:
        colors_rofi = [format_rofi_color_line(section) for section in line.split(',')]

        if 'normal' in line or 'urgent' in line or 'active' in line:
            line = line.replace(colors_rofi[1], new_color)
        new_lines.append(line)

    with open(rofi_path, 'w') as rofi_file:
        rofi_file.writelines(new_lines)
    logger.info("Successfully written new colors to rofi theme.")


def set_kitty_colors(colors, kitty_path):
    backup_file(kitty_path)

    logger.debug(f"Read kitty config file {kitty_path}.")
    with open(kitty_path, 'r') as kitty_file:
        lines = kitty_file.readlines()

    COLOR_REGEX = re.compile(r'^color(?P<color_num>\d\d?)\s(?P<color>#([0-9a-f]{6}|[0-9a-f]{3}))')
    new_lines = []
    for line in lines:
        color_match = COLOR_REGEX.match(line)
        if color_match:
            color_num = int(color_match.group('color_num'))
            new_color = colorz.hexify(colors[color_num if color_num <= 7 else color_num - 8][0if color_num <= 7 else 1])
            line = line.replace(color_match.group('color'), new_color)
        new_lines.append(line)

    with open(kitty_path, 'w') as kitty_file:
        kitty_file.writelines(new_lines)
    logger.info("Successfully written new colors to kitty config.")


def load_new_xrdb_colors():
    ret_val = subprocess.run(['xrdb', '-load', os.path.expanduser('~/.Xresources')])
    if ret_val.returncode == 0:
        logger.info("Successfully loaded new colors in xrdb.")
        return True
    logger.error("Failed loading new colors in xrdb.")
    return False


def set_new_background_image(img):
    ret_val = subprocess.run(['feh', '--bg-scale', img])
    if ret_val.returncode == 0:
        logger.info(f"Successfully set {img} as new background image.")
        return True
    logger.error(f"Failed setting {img} as new background image.")
    return False


def reload_polybar():
    # with subprocess.Popen(['polybar-make'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
    ret_val = subprocess.run(['polybar-make'], stdout=subprocess.DEVNULL)
    if ret_val.returncode == 0:
        logger.info("Successfully reloaded polybar.")
        return True
    logger.error(f"Failed reloading polybar.")
    return False


def reload_i3():
    i3 = Connection()
    ret_val = i3.command('reload')
    logger.debug(f"i3ipc reload command output: {ret_val}.")


@click.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option(
    '-c', '--xresources-color-file',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, writable=True),
    default=os.path.expanduser('~/.xcolors/my_colors'),
    help="Xresources file with color configuration."
)
@click.option(
    '-r', '--rofi-theme-file',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, writable=True),
    default=os.path.expanduser('~/.config/rofi/theme.rasi'),
    help="Rofi config file containing color config."
)
@click.option(
    '-k', '--kitty-config-file',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, writable=True),
    default=os.path.expanduser('~/.config/kitty/kitty.conf'),
    help="Kitty config file."
)
@click.option(
    '-o', '--orientation', default='horizontal',
    type=click.Choice(['horizontal', 'vertical'], case_sensitive=False),
    help="Choose screen orientation."
)
@click.option('-n', '--no-scaling', is_flag=True, help="Only consider images that fit the monitor size.")
@click.option(
    '-p', '--polybar-reload', is_flag=True,
    help=(
        "Reload polybar from script. "
        "CAREFUL: this makes python scripts started in polybar use this scripts python environment and might not work properly."
    )
)
@click.option('--debug/--no-debug', type=bool, help="Print debugging statements.")
@optgroup.group("Colorz configuration", help="Specify additional colorz options.")
@optgroup.option('--colorz-num-colors', type=int, default=8, help="number of colors to generate (excluding bold).")
@optgroup.option('--colorz-minv', type=click.IntRange(min=0, max=255), default=170, help="minimum value for the colors. Default: 170")
@optgroup.option('--colorz-maxv', type=click.IntRange(min=0, max=255), default=200, help="maximum value for the colors. Default: 200")
@optgroup.option('--colorz-bold', type=int, default=50, help="how much value to add for bold colors. Default: 50")
def main(image_path, xresources_color_file, rofi_theme_file, kitty_config_file, orientation, no_scaling, debug, polybar_reload, **colorz_params):
    set_logging(debug)
    img = get_image(image_path, orientation, no_scaling)
    logger.info(f"Selected image {img}")

    with open(img, 'rb') as img_file:
        colors = colorz.colorz(
            img_file,
            n=colorz_params['colorz_num_colors'],
            min_v=colorz_params['colorz_minv'],
            max_v=colorz_params['colorz_maxv'],
            bold_add=colorz_params['colorz_bold'],
        )

    set_colors(colors, xresources_color_file)
    set_rofi_colors(colors, rofi_theme_file)
    set_kitty_colors(colors, kitty_config_file)
    load_new_xrdb_colors()
    set_new_background_image(img)
    if polybar_reload:
        reload_polybar()
    reload_i3()


if __name__ == "__main__":
    main()

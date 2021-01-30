# mytheme
VERY rudimentary theming script which sets colorsfrom an image for i3, polybar, kitty and rofi

## Install
```
git clone git@github.com:lheimbs/mytheme.git
cd mytheme

python -m venv venv --system-site-packages
source ./venv/bin/activate

pip install -r requirements.txt
```

## Usage
```
mytheme.py [OPTIONS] IMAGE_PATH

Options:
  -c, --xresources-color-file FILE
                                  Xresources file with color configuration.
  -r, --rofi-theme-file FILE      Rofi config file containing color config.
  -k, --kitty-config-file FILE    Kitty config file.
  -o, --orientation [horizontal|vertical]
                                  Choose screen orientation.
  -n, --no-scaling                Only consider images that fit the monitor
                                  size.

  -p, --polybar-reload            Reload polybar from script. CAREFUL: this
                                  makes python scripts started in polybar use
                                  this scripts python environment and might
                                  not work properly.

  --debug / --no-debug            Print debugging statements.

  Colorz configuration:           Specify additional colorz options.
    --colorz-num-colors INTEGER   number of colors to generate (excluding
                                  bold).

    --colorz-minv INTEGER RANGE   minimum value for the colors. Default: 170
    --colorz-maxv INTEGER RANGE   maximum value for the colors. Default: 200
    --colorz-bold INTEGER         how much value to add for bold colors.
                                  Default: 50

  --help                          Show this message and exit.
```

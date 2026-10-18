#!/usr/bin/env python3
"""Run after `npx cap add android`. Brands the generated Android project:
FundTrail launcher icons, splash screen and theme colours."""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'android', 'app', 'src', 'main', 'res')
TEAL = (15, 118, 110)

icon = Image.open(os.path.join(ROOT, 'tools', 'icon-512.png')).convert('RGBA')
maskable = Image.open(os.path.join(ROOT, 'tools', 'icon-maskable-512.png')).convert('RGBA')


def sized(img, px):
    return img.resize((px, px), Image.LANCZOS)


def circle(img):
    px = img.size[0]
    mask = Image.new('L', (px * 4, px * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, px * 4 - 1, px * 4 - 1), fill=255)
    mask = mask.resize((px, px), Image.LANCZOS)
    out = Image.new('RGBA', (px, px), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


# Launcher icons: legacy square/round for old phones, foreground layer for adaptive icons.
for dens, px in {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}.items():
    d = os.path.join(RES, 'mipmap-' + dens)
    os.makedirs(d, exist_ok=True)
    sized(icon, px).save(os.path.join(d, 'ic_launcher.png'))
    circle(sized(icon, px)).save(os.path.join(d, 'ic_launcher_round.png'))
    sized(maskable, round(px * 108 / 48)).save(os.path.join(d, 'ic_launcher_foreground.png'))

adaptive = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
'''
any26 = os.path.join(RES, 'mipmap-anydpi-v26')
os.makedirs(any26, exist_ok=True)
for name in ('ic_launcher.xml', 'ic_launcher_round.xml'):
    with open(os.path.join(any26, name), 'w') as f:
        f.write(adaptive)

vals = os.path.join(RES, 'values')
os.makedirs(vals, exist_ok=True)
with open(os.path.join(vals, 'ic_launcher_background.xml'), 'w') as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            '    <color name="ic_launcher_background">#0F766E</color>\n</resources>\n')

# Remove the default vector icon layers so only ours are used.
for rel in ('drawable-v24/ic_launcher_foreground.xml', 'drawable/ic_launcher_background.xml'):
    p = os.path.join(RES, rel)
    if os.path.exists(p):
        os.remove(p)

# Splash screen: replace every default splash image with a teal screen and the FundTrail icon.
count = 0
for dirpath, _, files in os.walk(RES):
    if os.path.basename(dirpath).startswith('drawable') and 'splash.png' in files:
        p = os.path.join(dirpath, 'splash.png')
        w, h = Image.open(p).size
        canvas = Image.new('RGB', (w, h), TEAL)
        s = max(64, int(min(w, h) * 0.28))
        canvas.paste(sized(icon, s).convert('RGB'), ((w - s) // 2, (h - s) // 2))
        canvas.save(p)
        count += 1

# Theme colours (status bar etc.). These override the library defaults.
with open(os.path.join(RES, 'values', 'colors.xml'), 'w') as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            '    <color name="colorPrimary">#0F766E</color>\n'
            '    <color name="colorPrimaryDark">#0B5D57</color>\n'
            '    <color name="colorAccent">#F59E0B</color>\n</resources>\n')

# Notification (status bar) icon: a white trend line, as Android expects a single-colour shape.
drawable = os.path.join(RES, 'drawable')
os.makedirs(drawable, exist_ok=True)
with open(os.path.join(drawable, 'ic_stat_fundtrail.xml'), 'w') as f:
    f.write('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:strokeColor="#FFFFFF" android:strokeWidth="2.4"
        android:strokeLineCap="round" android:strokeLineJoin="round"
        android:pathData="M3,18 L9,12 L13,15 L21,6"/>
    <path android:fillColor="#FFFFFF"
        android:pathData="M21,6 m-2.2,0 a2.2,2.2 0 1,0 4.4,0 a2.2,2.2 0 1,0 -4.4,0"/>
</vector>
''')

# Allow exact alarms so the 5 pm reminder arrives on time (the user grants it once in Settings).
mp = os.path.join(ROOT, 'android', 'app', 'src', 'main', 'AndroidManifest.xml')
with open(mp) as f:
    m = f.read()
perm = '<uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />'
if perm not in m:
    m = m.replace('</manifest>', '    ' + perm + '\n</manifest>')
    with open(mp, 'w') as f:
        f.write(m)

print('Branding applied (%d splash images replaced).' % count)

# Pantheon Core Visualization

## Run locally

```bash
cd /Users/alijawadfatmi/pantheon/ui/core_viz
python -m http.server 8787
```

Open: `http://127.0.0.1:8787/pantheon_core_panel.html`

## Automated verification

```bash
cd /Users/alijawadfatmi/pantheon
node ui/core_viz/verify_core_viz.mjs
```

## Fallback ladder

1. `webgl` bloom mode
2. `webgl-wireframe` (shader fallback)
3. `canvas2d`
4. `svg-static`
5. `unicode`

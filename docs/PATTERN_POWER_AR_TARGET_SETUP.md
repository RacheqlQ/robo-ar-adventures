# Pattern Power! AR target setup

## First tracking target

Use the PDF-extracted image named `printed_page_5_the_mixed_up_pattern.png` for the first target. It corresponds to the book's printed page 5, “The Mixed-Up Pattern” (PDF page 9).

The companion app currently expects a compiled MindAR image-target file (`.mind`) selected in its target upload control. The extracted PNG is **not** itself a `.mind` file.

## Compile the target

1. Download the target-image ZIP attached in the ChatGPT conversation: `pattern_power_ar_targets.zip`.
2. Extract it and select only `printed_page_5_the_mixed_up_pattern.png` for the first compile.
3. Open the official MindAR Image Targets Compiler: https://hiukim.github.io/mind-ar-js-doc/tools/compile/
4. Upload that PNG, run compilation, and download the generated `.mind` file.
5. Keep the generated file intact; do not rename it to `.png` or edit its bytes.

## Test in the feature branch first

1. Open the feature preview / branch page, not the production site.
2. Select the generated `.mind` file in the app's target-file control.
3. Start AR and grant camera access.
4. Point the camera at the **printed page 5** in the physical book or a full-size print of that page.
5. Confirm the target-found status appears, then test the “Fix the pattern bug” button and reset.
6. Repeat on an actual iPhone Safari and an Android Chrome device if available.

## Important constraints

- The compiler output has not been generated or tested by this repository commit; the browser compiler step must be completed first.
- Keep production unchanged until target recognition, camera permissions, the pattern interaction, and mobile layout pass.
- Start with one target. Add more book pages only after the first target is reliable; each target's index must match the target order in the compiled `.mind` file.
- The printed page artwork is the tracking target. Do not use the PDF cover or a cropped/redrawn substitute for the first test.

# OCR hero cleanup

Built-in image generation edit of `public/blog/beyond-ocr-scores/hero-ocr-watercolor.png`. Output:
`public/blog/beyond-ocr-scores/hero-ocr-watercolor-polished.png`.

## Prompt

```text
Use case: precise-object-edit.
Asset: existing watercolor editorial hero about OCR difficulty.
Input image 1 is the edit target. Polish it with ONLY these two local cleanups:

1. Completely remove the thin rust-red horizontal reading-order arrow/loop running across the upper text columns. It begins below "Each specimen was measured twice", runs across the gutter to the right column, bends down, then runs back across another line. Remove BOTH horizontal strokes, the right-hand vertical bend, and ALL arrowheads/end marks. Restore uninterrupted warm watercolor paper behind it. Preserve every nearby letter and the subtle vertical column divider. The two text columns should be clean and easy to read.
2. Remove the isolated short red vertical stroke in the blank lower-right corner of the left source sheet (beside the footnotes). Restore the paper there.

Keep EVERYTHING ELSE unchanged: the wide composition, warm ivory watercolor paper, delicate ink texture, dimensions, margins, source document, all exact readable words, numbered feature badges 01–04, all four OCR failure examples, two-column layout, table borders and merged headers, table values A 12 15 / B 24 28 / C 36 41, mathematically correct source fraction and summation notation, deliberately flattened OCR equation, handwritten "recheck B / use original" and its curved arrow to row B, fine-print footnotes, subtle red bracket over the merged table header, and the small central arrow connecting the source sheet to the OCR attempt.
Preserve sharp letterforms, do not reword or abbreviate text, do not invent additional annotations. No new arrows, underlines, labels, content, props, or article title. This is a careful cleanup of the supplied image, not a redesign. Keep the same aspect ratio and full uncropped frame.
```

# Compare design quality fairly

Use this protocol when deciding whether a workflow change improves generated interfaces. A detector count or a single model's opinion is not evidence that one design is more beautiful. Evaluate the actual rendered pages against the same brief and implementation constraints.

## Set up a fair comparison

1. Select three to six briefs from different page types. Keep each brief specific enough to imply real content and a user task, but don't prescribe the visual direction.
2. Fix the tool/model version, prompt, project files, assets, runtime, viewport sizes, and available time. Change only the design workflow being evaluated.
3. Give each workflow a clean copy of the same starter project. Don't let one version see the other version's output or private scoring notes.
4. Capture full-page desktop and mobile renders at the same sizes. Keep source and output files under anonymous labels such as A/B until the review is finished.
5. Ask at least two reviewers who did not generate the pages to review them independently. Randomize which variant they see first.

## Judge the rendered page

For each brief and each variant, write a short evidence note and mark each dimension as **strong**, **mixed**, or **weak**. Use the brief to decide which dimensions matter most; do not average everything into a single beauty score.

- **Purpose and task:** Can the intended user quickly understand what this page does and what action is available?
- **Identity and specificity:** Does the design visibly belong to this product, audience, and content, or could the same page be relabeled unchanged?
- **Hierarchy and composition:** Is the first read clear? Do scale, alignment, density, spacing, image crop, and section rhythm support it?
- **Content and credibility:** Are the important product details present? Are data and claims coherent, sourced, and clearly marked as sample when invented?
- **Visual coherence:** Do type, color, surface, graphics, and interaction states support one visual premise?
- **Responsive behavior:** Does mobile feel deliberately rearranged and usable? Check text wrapping, overflow, navigation, controls, and chart/table readability.
- **Interaction and accessibility:** Do controls work, keyboard focus show, names exist for non-text controls, and contrast/reduced motion receive appropriate attention?
- **Finish:** Note concrete visual defects such as collisions, broken assets, cramped controls, inconsistent alignment, or unfinished states.

A reviewer should identify which element they looked at and why it helps or hurts the brief. “Looks polished” and detector counts alone are not actionable evidence.

## Record the result

Use one row per brief and variant. Preserve the screenshots, prompt, code, versions, and notes so a later run can be compared honestly.

| Brief | Variant | Purpose | Identity | Composition | Credibility | Responsive | Interaction/accessibility | Evidence note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Example: neighborhood clinic appointment page | A | mixed | weak | strong | mixed | weak | mixed | Mobile hero hides the booking action below an oversized photo. |

After unblinding, compare paired judgments. Summarize which workflow won on which dimensions, where reviewers disagreed, and any regression that would block adoption. Do not claim general superiority from one prompt, one reviewer, or a model-generated score. Repeat with new briefs before treating a pattern as reliable.

## Starter brief set

These are deliberately different tasks and should be adapted to a real product before using them as a benchmark:

1. **Local service:** A neighborhood bicycle repair shop needs a page for hours, same-day repairs, service pricing, and directions.
2. **Data-heavy tool:** A small energy team needs to spot unusual building use and decide which site to investigate today.
3. **Editorial:** A public garden needs a readable field guide to three native plants, including seasonal identification details.
4. **Commerce:** A ceramics studio needs shoppers to compare two mug sizes, glaze options, shipping, and care instructions.
5. **Mobile utility:** A volunteer coordinator needs to check in attendees, see who is missing, and record an accessibility request on a phone.
6. **Portfolio:** An early-career sound designer needs to show three projects, explain their role, and make contact easy without invented client metrics.

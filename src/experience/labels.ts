export type LabelSide = 'below' | 'above';
export type LabelPlacement = LabelSide | 'hidden';

export interface LabelItem {
  id: string;
  x: number;
  y: number;
  bodyRadius: number;
  labelRadius: number;
  halfWidth: number;
  height: number;
  priority: number;
  prefer: LabelSide;
}

export interface LabelResult {
  placement: LabelPlacement;
  nudge: number;
}

interface Rect {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export const LABEL_GAP = 10;
const EDGE = 10;

const rectsOverlap = (a: Rect, b: Rect) =>
  a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;

const rectHitsDisc = (rect: Rect, x: number, y: number, radius: number) => {
  const dx = x - Math.max(rect.left, Math.min(x, rect.right));
  const dy = y - Math.max(rect.top, Math.min(y, rect.bottom));
  return dx * dx + dy * dy < radius * radius;
};

function labelRect(item: LabelItem, side: LabelSide, width: number) {
  const fits = item.halfWidth * 2 + EDGE * 2 <= width;
  const center = fits
    ? Math.max(
        item.halfWidth + EDGE,
        Math.min(item.x, width - item.halfWidth - EDGE),
      )
    : item.x;
  const offset = item.labelRadius + LABEL_GAP;
  const top =
    side === 'below' ? item.y + offset : item.y - offset - item.height;
  return {
    nudge: center - item.x,
    rect: {
      left: center - item.halfWidth,
      right: center + item.halfWidth,
      top,
      bottom: top + item.height,
    },
  };
}

export function resolveLabels(
  items: LabelItem[],
  viewportWidth: number,
  previous?: ReadonlyMap<string, LabelPlacement>,
) {
  const results = new Map<string, LabelResult>();
  const placed: Rect[] = [];
  const ordered = [...items].sort((a, b) => b.priority - a.priority);

  for (const item of ordered) {
    const last = previous?.get(item.id);
    const first: LabelSide =
      last === 'below' || last === 'above' ? last : item.prefer;
    const sides: LabelSide[] = [first, first === 'below' ? 'above' : 'below'];
    let result: LabelResult = { placement: 'hidden', nudge: 0 };

    for (const side of sides) {
      const { rect, nudge } = labelRect(item, side, viewportWidth);
      const blocked =
        placed.some((other) => rectsOverlap(rect, other)) ||
        items.some(
          (other) =>
            other !== item &&
            rectHitsDisc(rect, other.x, other.y, other.bodyRadius),
        );
      if (blocked) continue;
      placed.push(rect);
      result = { placement: side, nudge };
      break;
    }
    results.set(item.id, result);
  }
  return results;
}

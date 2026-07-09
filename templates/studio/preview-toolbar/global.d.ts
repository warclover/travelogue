/**
 * Preview toolbar · ambient globals and DOM shims (M-C5 tsc gate baseline).
 * Extend incrementally; remove shims as modules gain precise types.
 */

declare function studioModal(opts: Record<string, unknown>): Promise<boolean>;
declare function studioToast(msg: string, opts?: Record<string, unknown>): void;

interface Window {
  TravelogueLenis?: {
    stop?: () => void;
    start?: () => void;
    pause?: () => void;
    resume?: () => void;
  };
  TravelogueLongshot?: Record<string, unknown>;
  TravelogueBreath?: { init?: () => void; destroy?: () => void };
  travelogueApplyPhotosOnly?: (on: boolean) => void;
  __TRAVELOGUE_READING__?: {
    profile?: string;
    scroll?: { folio?: string };
  };
}

interface Element {
  hidden: boolean;
  disabled: boolean;
  value: string;
  checked: boolean;
  open: boolean;
  readonly style: CSSStyleDeclaration;
  readonly dataset: DOMStringMap;
  title: string;
  focus(options?: FocusOptions): void;
  _sheet?: {
    open: (tab: string) => void;
    setPendingDot?: (on: boolean) => void;
    refreshLayoutTab?: () => void;
  };
  _taskDock?: { hide: () => void; [key: string]: unknown };
  _exportDockActive?: boolean;
  _exportResultShowing?: boolean;
}

interface HTMLDivElement {
  _progressFill?: HTMLElement;
  _mainEl?: HTMLElement;
  _subEl?: HTMLElement;
}

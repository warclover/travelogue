/**
 * Preview toolbar · ambient globals and DOM shims (M-C5 tsc gate baseline).
 * Extend incrementally; remove shims as modules gain precise types.
 */

declare function studioModal(opts: Record<string, unknown>): Promise<boolean | string>;
declare function studioToast(msg: string, opts?: Record<string, unknown>): void;

declare module "/__studio/js/llm-settings.js" {
  export function openLlmSettings(opts?: Record<string, unknown>): void;
}

declare module "/__studio/js/help-drawer.js" {
  export function openHelpDrawer(opts?: Record<string, unknown>): void;
  export function closeHelpDrawer(): void;
  export function isHelpDrawerOpen(): boolean;
  export function configureHelpDrawer(opts?: Record<string, unknown>): void;
}

interface Error {
  job?: unknown;
}

interface EventTarget {
  getAttribute?(qualifiedName: string): string | null;
  closest?(selectors: string): Element | null;
}

interface Window {
  TravelogueLenis?: {
    stop?: () => void;
    start?: () => void;
    pause?: () => void;
    resume?: () => void;
    scrollTo?: (target: unknown, opts?: unknown) => void;
  };
  TravelogueLongshot?: Record<string, unknown>;
  TravelogueBreath?: { init?: () => void; destroy?: () => void };
  travelogueApplyPhotosOnly?: (on: boolean) => void;
  travelogueTelemetry?: {
    track?: (...args: unknown[]) => void;
    [key: string]: unknown;
  };
  __TRAVELOGUE_READING__?: {
    profile?: string;
    scroll?: { folio?: string };
  };
  /** SNR · CTA label dedupe key (longshot.js) */
  __snrCtaLabelKey?: string;
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
  src?: string;
  onload?: ((this: GlobalEventHandlers, ev: Event) => any) | null;
  onerror?: OnErrorEventHandler;
  contentDocument?: Document | null;
  focus(options?: FocusOptions): void;
  _sheet?: {
    open: (tab: string) => void;
    setPendingDot?: (on: boolean) => void;
    refreshLayoutTab?: () => void;
    isOpen?: () => boolean;
    close?: (reason?: string, done?: () => void) => void;
    [key: string]: unknown;
  };
  _taskDock?: { hide: () => void; [key: string]: unknown };
  _exportDockActive?: boolean;
  _exportResultShowing?: boolean;
  _savedMarkTimer?: ReturnType<typeof setTimeout>;
  _panelDraft?: { getDraft?: () => Record<string, unknown>; [key: string]: unknown };
  _chapterPanel?: { isOpen?: () => boolean; close?: () => void; [key: string]: unknown };
  _aiSheet?: {
    open?: (opts?: Record<string, unknown>) => void;
    close?: (reason?: string, done?: () => void) => void;
    isOpen?: () => boolean;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

interface HTMLElement {
  /** AI Sheet API mounted on preview toolbar root (SNR / chapter panel). */
  _aiSheet?: {
    open?: (opts?: Record<string, unknown>) => void;
    close?: (reason?: string, done?: () => void) => void;
    isOpen?: () => boolean;
    [key: string]: unknown;
  };
}

interface HTMLInputElement {
  isComposing?: boolean;
}

interface HTMLDivElement {
  _progressFill?: HTMLElement;
  _progressEl?: HTMLElement;
  _mainEl?: HTMLElement;
  _subEl?: HTMLElement;
}

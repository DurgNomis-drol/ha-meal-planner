
import { mdiAlertCircle, mdiHomeAssistant, mdiInformation, mdiOpenInNew } from "@mdi/js";
import "@polymer/app-layout/app-header-layout/app-header-layout";
import "@polymer/app-layout/app-header/app-header";
import "@polymer/app-layout/app-toolbar/app-toolbar";
import "@polymer/paper-item/paper-icon-item";
import "@polymer/paper-item/paper-item-body";
import { css, CSSResultGroup, html, LitElement, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators";
import { isComponentLoaded } from "../../homeassistant-frontend/src/common/config/is_component_loaded";
import { navigate } from "../../homeassistant-frontend/src/common/navigate";
import { computeRTL } from "../../homeassistant-frontend/src/common/util/compute_rtl";
import "../../homeassistant-frontend/src/components/ha-alert";
import "../../homeassistant-frontend/src/components/ha-card";
import "../../homeassistant-frontend/src/components/ha-menu-button";
import "../../homeassistant-frontend/src/components/ha-svg-icon";
import "../../homeassistant-frontend/src/panels/config/ha-config-section";
import { haStyle } from "../../homeassistant-frontend/src/resources/styles";
import { HomeAssistant, Route } from "../../homeassistant-frontend/src/types";

@customElement("cookbook-frontend")
export class CookBook extends LitElement {

  @property({ attribute: false }) public hass!: HomeAssistant;

  @property({ attribute: false }) public route!: Route;

  @property({ type: Boolean }) public isWide!: boolean;

  @property({ type: Boolean }) public narrow!: boolean;

  protected render(): TemplateResult | void {

    return html`
      <app-header-layout has-scrolling-region>
        <app-header fixed slot="header">
          <app-toolbar>
            <div main-title>CookBook</div>
            <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
          </app-toolbar>
        </app-header>
      </app-header-layout>
    `;
  }


  static get styles(): CSSResultGroup {
    return [
      haStyle,
      css`
        paper-icon-item {
          cursor: pointer;
        }
        paper-icon-item[information] {
          cursor: normal;
        }
        app-header-layout {
          display: contents;
        }
        app-header,
        app-toolbar,
        ha-menu-button {
          color: var(--secondary-text-color);
          background-color: var(--primary-background-color);
          --app-header-background-color: var(--primary-background-color);
        }
        ha-svg-icon {
          color: var(--secondary-text-color);
        }
        ha-config-section {
          color: var(--primary-text-color);
          padding-bottom: 24px;
          margin-top: -24px;
        }
        paper-item-body {
          width: 100%;
          min-height: var(--paper-item-body-two-line-min-height, 72px);
          display: var(--layout-vertical_-_display);
          flex-direction: var(--layout-vertical_-_flex-direction);
          justify-content: var(--layout-center-justified_-_justify-content);
        }
        paper-item-body {
          color: var(--hcv-text-color-primary);
        }
        paper-item-body div {
          font-size: 14px;
          color: var(--hcv-text-color-secondary);
        }
        div[secondary] {
          white-space: normal;
        }
      `,
    ];
  }
}
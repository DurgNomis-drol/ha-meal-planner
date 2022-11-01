import {
    LitElement,
    html,
    css,
  } from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";
  
  class CookBook extends LitElement {
    static get properties() {
      return {
        hass: { type: Object },
        narrow: { type: Boolean },
        route: { type: Object },
        panel: { type: Object },
      };
    }
  
    render() {
      return html`
          <div class="body">
              <h1>CookBook</h1>
              <div class="recipe-list">
                  <ul>
                      <li>Test</li>
                      <li>Test</li>
                      <li>Test</li>
                      <li>Test</li>
                      <li>Test</li>
                      <li>Test</li>
                      <li>Test</li>
                      <li>Test</li>
                  </ul>
              </div>
          </div>
      `;
    }
  
    static get styles() {
      return css`
        :host {
          background-color: #fafafa;
          padding: 16px;
          display: block;
        }
        wired-card {
          background-color: white;
          padding: 16px;
          display: block;
          font-size: 18px;
          max-width: 600px;
          margin: 0 auto;
        }
      `;
    }
  }
  customElements.define("cookbook-frontend", CookBook);
/*
  Ad campaign attribution

  When someone arrives from one of our ads, remember which platform sent them
  and pass that campaign code along to Tito when they go buy a ticket. That's
  the whole scope: one first-party cookie holding one campaign code, no
  third-party pixels, nothing about who the visitor is.

  See /privacy/ — the "Cookies" section describes exactly this behavior.
*/
(() => {
  const COOKIE_NAME = 'dcus_campaign';
  const COOKIE_DAYS = 30;

  // Query param Tito reads for source attribution.
  const TITO_PARAM = 'source';

  /*
    Campaign codes as configured in Tito.
  */
  const CAMPAIGNS = [
    {
      code: 'dcusli26',
      // LinkedIn appends li_fat_id to ad clicks.
      clickIds: ['li_fat_id'],
      utmSources: ['linkedin', 'linkedin-ads', 'li'],
    },
    {
      code: 'dcusrd26',
      // Reddit appends rdt_cid to ad clicks.
      clickIds: ['rdt_cid'],
      utmSources: ['reddit', 'reddit-ads', 'rdt'],
    },
    {
      code: 'dcusgg26',
      // Google appends gclid, or gbraid/wbraid when consent limits gclid.
      clickIds: ['gclid', 'gbraid', 'wbraid'],
      utmSources: ['google', 'google-ads', 'googleads', 'adwords'],
    },
  ];

  const readCookie = (name) => {
    const match = document.cookie.match(
      new RegExp('(?:^|; )' + name + '=([^;]*)')
    );
    return match ? decodeURIComponent(match[1]) : null;
  };

  const writeCookie = (name, value, days) => {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    const secure = location.protocol === 'https:' ? '; Secure' : '';
    document.cookie =
      `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax${secure}`;
  };

  /*
    Identify the campaign from the landing URL.

    Platform click IDs come first: the ad platforms append them automatically,
    so they're a definitive paid-click signal even if a UTM tag was missed.
    utm_source is the fallback for hand-tagged ads.

    We deliberately don't fall back to the referrer — an organic Google search
    or an organic Reddit/LinkedIn post arrives with the same referrer as an ad,
    and attributing those to a paid campaign would pollute the numbers.
  */
  const detectCampaign = (params) => {
    for (const campaign of CAMPAIGNS) {
      if (campaign.clickIds.some((id) => params.get(id))) {
        return campaign.code;
      }
    }

    // Respect an explicit organic tag rather than counting it as paid.
    if ((params.get('utm_medium') || '').toLowerCase() === 'organic') {
      return null;
    }

    const utmSource = (params.get('utm_source') || '').toLowerCase().trim();

    if (utmSource) {
      const matched = CAMPAIGNS.find((campaign) =>
        campaign.utmSources.includes(utmSource)
      );

      if (matched) {
        return matched.code;
      }
    }

    return null;
  };

  const isTitoLink = (anchor) => {
    const host = anchor.hostname.toLowerCase();
    return host === 'ti.to' || host.endsWith('.ti.to');
  };

  /*
    Stamp the campaign code onto every Tito link on the page. A code already
    hardcoded in the markup wins — we never overwrite it.
  */
  const tagTitoLinks = (code) => {
    document.querySelectorAll('a[href]').forEach((anchor) => {
      if (!isTitoLink(anchor)) return;

      try {
        const url = new URL(anchor.href);

        if (url.searchParams.has(TITO_PARAM)) return;

        url.searchParams.set(TITO_PARAM, code);
        anchor.href = url.toString();
      } catch {
        // Malformed href — leave it alone.
      }
    });
  };

  const params = new URLSearchParams(location.search);
  const detected = detectCampaign(params);

  if (detected) {
    writeCookie(COOKIE_NAME, detected, COOKIE_DAYS);
  }

  /*
    Use the code from this visit if there is one, otherwise the one stored from
    an earlier ad click. Most recent ad click wins, and a direct visit never
    clears or sets the cookie — detection only ever reads the current URL.
  */
  const code = detected || readCookie(COOKIE_NAME);

  if (!code) return;

  // Guard against a stale or tampered cookie value.
  if (!CAMPAIGNS.some((campaign) => campaign.code === code)) return;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => tagTitoLinks(code));
  } else {
    tagTitoLinks(code);
  }
})();

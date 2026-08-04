import { pathToFileURL } from 'node:url';
import { addonBuilder, serveHTTP } from 'stremio-addon-sdk';
import channels from './channels.json' with { type: 'json' };
import blacklist from './blacklist.config.json' with { type: 'json' };

const PORT = Number.parseInt(process.env.PORT || '7000', 10);
const HOST = process.env.HOST || '0.0.0.0';

const catalogDefinitions = [
  { id: 'official-tv-all', name: 'TV officielle — Toutes', category: null },
  { id: 'official-tv-information', name: 'TV officielle — Information', category: 'Information' },
  { id: 'official-tv-culture', name: 'TV officielle — Culture', category: 'Culture' },
  { id: 'official-tv-generaliste', name: 'TV officielle — Généralistes', category: 'Généraliste' }
];

export const manifest = {
  id: 'community.niakvio.official-tv',
  version: '1.1.0',
  name: 'Niakvio TV officielle',
  description: 'Chaînes gratuites accessibles depuis les services officiels de leurs éditeurs.',
  logo: 'https://raw.githubusercontent.com/niakw/Niakvio/main/assets/branding/nuvio-providers-logo.png',
  resources: [
    { name: 'catalog', types: ['tv'] },
    { name: 'meta', types: ['tv'], idPrefixes: ['niakvio-tv:'] },
    { name: 'stream', types: ['tv'], idPrefixes: ['niakvio-tv:'] }
  ],
  types: ['tv'],
  catalogs: catalogDefinitions.map(({ id, name }) => ({
    type: 'tv',
    id,
    name,
    extra: [{ name: 'search', isRequired: false }]
  })),
  idPrefixes: ['niakvio-tv:'],
  behaviorHints: {
    configurable: false,
    configurationRequired: false
  }
};

function normalize(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('fr')
    .trim();
}

function getHostname(value) {
  if (!value) return null;
  try {
    return new URL(value).hostname.toLocaleLowerCase('fr').replace(/^www\./, '');
  } catch {
    return null;
  }
}

function hostIsBlocked(hostname) {
  if (!hostname) return false;
  return blacklist.blockedHosts.some((blockedHost) => {
    const blocked = normalize(blockedHost);
    return hostname === blocked || hostname.endsWith(`.${blocked}`);
  });
}

export function getBlockReason(channel) {
  if (!channel || typeof channel !== 'object') return 'invalid-channel';
  if (blacklist.blockedIds.includes(channel.id)) return 'blocked-id';

  const normalizedName = normalize(channel.name);
  if (
    blacklist.blockedNamePatterns.some((pattern) => {
      try {
        return new RegExp(pattern, 'i').test(normalizedName);
      } catch {
        return true;
      }
    })
  ) {
    return 'blocked-name';
  }

  const urls = [channel.officialPage, channel.directUrl].filter(Boolean);
  if (urls.some((url) => hostIsBlocked(getHostname(url)))) return 'blocked-host';
  if (blacklist.requireVerified && channel.verified !== true) return 'unverified';
  if (blacklist.requireOfficialPage && !channel.officialPage) return 'missing-official-page';
  if (!getHostname(channel.officialPage)) return 'invalid-official-page';

  return null;
}

export const allowedChannels = Object.freeze(channels.filter((channel) => !getBlockReason(channel)));

function findChannel(id) {
  return allowedChannels.find((channel) => channel.id === id) || null;
}

function toMeta(channel) {
  return {
    id: `niakvio-tv:${channel.id}`,
    type: 'tv',
    name: channel.name,
    poster: channel.poster,
    posterShape: 'square',
    description: channel.description,
    genres: [channel.category],
    releaseInfo: 'En direct',
    videos: [
      {
        id: `niakvio-tv:${channel.id}:live`,
        title: `${channel.name} — Direct`,
        released: new Date(0).toISOString()
      }
    ],
    behaviorHints: {
      defaultVideoId: `niakvio-tv:${channel.id}:live`
    }
  };
}

export function selectCatalog(catalogId, search = '') {
  const definition = catalogDefinitions.find((item) => item.id === catalogId);
  if (!definition) return [];

  const query = normalize(search);
  return allowedChannels.filter((channel) => {
    if (definition.category && channel.category !== definition.category) return false;
    if (!query) return true;
    return normalize(`${channel.name} ${channel.category} ${channel.description}`).includes(query);
  });
}

export const builder = new addonBuilder(manifest);

builder.defineCatalogHandler(async ({ id, extra = {} }) => ({
  metas: selectCatalog(id, extra.search).map(toMeta),
  cacheMaxAge: 300
}));

builder.defineMetaHandler(async ({ id }) => {
  const channelId = String(id).replace(/^niakvio-tv:/, '').replace(/:live$/, '');
  const channel = findChannel(channelId);
  return { meta: channel ? toMeta(channel) : null, cacheMaxAge: 300 };
});

builder.defineStreamHandler(async ({ id }) => {
  const channelId = String(id).replace(/^niakvio-tv:/, '').replace(/:live$/, '');
  const channel = findChannel(channelId);
  if (!channel) return { streams: [] };

  if (channel.directUrl) {
    return {
      streams: [
        {
          name: 'Flux officiel',
          title: `${channel.name} — direct officiel`,
          url: channel.directUrl,
          behaviorHints: { notWebReady: false }
        }
      ],
      cacheMaxAge: 60
    };
  }

  return {
    streams: [
      {
        name: 'Site officiel',
        title: `${channel.name} — ouvrir le direct officiel`,
        externalUrl: channel.officialPage
      }
    ],
    cacheMaxAge: 300
  };
});

export function startServer() {
  serveHTTP(builder.getInterface(), { port: PORT, host: HOST, cacheMaxAge: 300 });
  console.log(`Niakvio Official TV addon listening on http://${HOST}:${PORT}/manifest.json`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  startServer();
}

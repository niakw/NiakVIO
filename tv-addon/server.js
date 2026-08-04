import { addonBuilder, serveHTTP } from 'stremio-addon-sdk';
import channels from './channels.json' with { type: 'json' };
import blacklist from './blacklist.config.json' with { type: 'json' };

const PORT = Number.parseInt(process.env.PORT || '7000', 10);
const HOST = process.env.HOST || '0.0.0.0';

const blockedIds = new Set(blacklist.blockedIds || []);
const blockedPatterns = (blacklist.blockedNamePatterns || []).map(
  (pattern) => new RegExp(pattern, 'i')
);
const blockedHosts = new Set(
  (blacklist.blockedHosts || []).map((host) => String(host).toLowerCase())
);

function getHostname(value) {
  if (!value) return null;
  try {
    return new URL(value).hostname.toLowerCase();
  } catch {
    return null;
  }
}

function isBlockedHost(value) {
  const hostname = getHostname(value);
  if (!hostname) return false;
  return [...blockedHosts].some(
    (blockedHost) => hostname === blockedHost || hostname.endsWith(`.${blockedHost}`)
  );
}

function isAllowedChannel(channel) {
  if (!channel || blockedIds.has(channel.id)) return false;
  if (blockedPatterns.some((pattern) => pattern.test(channel.name || ''))) return false;
  if (blacklist.requireVerified && channel.verified !== true) return false;
  if (blacklist.requireOfficialPage && !channel.officialPage) return false;
  if (isBlockedHost(channel.officialPage) || isBlockedHost(channel.directUrl)) return false;
  return true;
}

const allowedChannels = channels.filter(isAllowedChannel);

const manifest = {
  id: 'community.niakvio.official-tv',
  version: '1.0.0',
  name: 'Niakvio TV officielle',
  description: 'Chaînes TV gratuites accessibles depuis leurs services officiels.',
  logo: 'https://raw.githubusercontent.com/niakw/Niakvio/main/assets/branding/nuvio-providers-logo.png',
  resources: ['catalog', 'meta', 'stream'],
  types: ['tv'],
  catalogs: [
    {
      type: 'tv',
      id: 'official-tv',
      name: 'TV officielle',
      extra: [{ name: 'search', isRequired: false }]
    }
  ],
  idPrefixes: ['niakvio-tv:'],
  behaviorHints: {
    configurable: false,
    configurationRequired: false
  }
};

const builder = new addonBuilder(manifest);

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
    behaviorHints: {
      defaultVideoId: `niakvio-tv:${channel.id}:live`
    }
  };
}

builder.defineCatalogHandler(async ({ extra = {} }) => {
  const query = String(extra.search || '').trim().toLocaleLowerCase('fr');
  const selected = query
    ? allowedChannels.filter((channel) =>
        `${channel.name} ${channel.category}`.toLocaleLowerCase('fr').includes(query)
      )
    : allowedChannels;

  return { metas: selected.map(toMeta) };
});

builder.defineMetaHandler(async ({ id }) => {
  const channelId = String(id).replace(/^niakvio-tv:/, '');
  const channel = allowedChannels.find((item) => item.id === channelId);
  return { meta: channel ? toMeta(channel) : null };
});

builder.defineStreamHandler(async ({ id }) => {
  const channelId = String(id)
    .replace(/^niakvio-tv:/, '')
    .replace(/:live$/, '');
  const channel = allowedChannels.find((item) => item.id === channelId);

  if (!channel) return { streams: [] };

  if (channel.directUrl) {
    return {
      streams: [
        {
          name: 'Flux officiel',
          title: `${channel.name} — direct officiel`,
          url: channel.directUrl,
          behaviorHints: {
            notWebReady: false
          }
        }
      ]
    };
  }

  return {
    streams: [
      {
        name: 'Lecteur officiel',
        title: `${channel.name} — ouvrir le direct officiel`,
        externalUrl: channel.officialPage
      }
    ]
  };
});

serveHTTP(builder.getInterface(), { port: PORT, host: HOST });
console.log(
  `Niakvio Official TV addon listening on http://${HOST}:${PORT}/manifest.json (${allowedChannels.length}/${channels.length} channels allowed)`
);

import { addonBuilder, serveHTTP } from 'stremio-addon-sdk';
import channels from './channels.json' with { type: 'json' };

const PORT = Number.parseInt(process.env.PORT || '7000', 10);
const HOST = process.env.HOST || '0.0.0.0';

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
    ? channels.filter((channel) =>
        `${channel.name} ${channel.category}`.toLocaleLowerCase('fr').includes(query)
      )
    : channels;

  return { metas: selected.map(toMeta) };
});

builder.defineMetaHandler(async ({ id }) => {
  const channelId = String(id).replace(/^niakvio-tv:/, '');
  const channel = channels.find((item) => item.id === channelId);
  return { meta: channel ? toMeta(channel) : null };
});

builder.defineStreamHandler(async ({ id }) => {
  const channelId = String(id)
    .replace(/^niakvio-tv:/, '')
    .replace(/:live$/, '');
  const channel = channels.find((item) => item.id === channelId);

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
console.log(`Niakvio Official TV addon listening on http://${HOST}:${PORT}/manifest.json`);

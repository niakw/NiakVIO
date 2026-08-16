import { adaptRequestForDevice, normalizeStreamCandidate } from "./contracts.mjs";

export const DEVICE_CAPABILITIES = Object.freeze({
  worker: Object.freeze({ subtitles: true, headers: true, positionalGetStreams: true }),
  mobile: Object.freeze({ subtitles: true, headers: true, positionalGetStreams: true }),
  desktop: Object.freeze({ subtitles: true, headers: true, positionalGetStreams: true }),
  tv: Object.freeze({ subtitles: false, headers: true, positionalGetStreams: true }),
});

export function toRuntimeInvocation(request, device) {
  const adapted = adaptRequestForDevice(request, device);
  return {
    device,
    functionName: adapted.call,
    positionalArgs: adapted.args,
    settings: adapted.settings,
    canonicalRequest: adapted.canonical,
    capabilities: DEVICE_CAPABILITIES[device],
  };
}

export function toRuntimeStream(candidate, device, context = {}) {
  const capabilities = DEVICE_CAPABILITIES[device];
  if (!capabilities) throw new Error(`unsupported device: ${device}`);
  const stream = normalizeStreamCandidate(candidate, context);
  const runtime = {
    title: stream.title,
    name: stream.name,
    url: stream.url,
    quality: stream.quality,
    size: stream.size,
    language: stream.language,
    provider: stream.provider,
    type: stream.type,
    headers: capabilities.headers && Object.keys(stream.headers).length ? stream.headers : undefined,
  };
  if (capabilities.subtitles && stream.subtitles.length) runtime.subtitles = stream.subtitles;
  return runtime;
}

export function compareDeviceInvocations(request) {
  const devices = ["mobile", "desktop", "tv"];
  const invocations = Object.fromEntries(devices.map((device) => [device, toRuntimeInvocation(request, device)]));
  const signatures = new Set(devices.map((device) => JSON.stringify(invocations[device].positionalArgs)));
  return {
    consistent: signatures.size === 1,
    invocations,
  };
}

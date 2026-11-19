import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.Proxy;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import okhttp3.Dns;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public final class WafOkHttpProbe {
    private static final Set<String> SAFE_REQUEST_HEADERS = Set.of(
        "accept", "accept-language", "content-type", "origin", "referer", "referrer",
        "user-agent", "x-requested-with", "x-client-version", "x-app-version"
    );
    private static final String[] CHALLENGE_MARKERS = new String[] {
        "just a moment",
        "checking your browser",
        "verify you are human",
        "attention required",
        "captcha",
        "challenge-platform",
        "cf-browser-verification",
        "security check",
        "turnstile"
    };

    private static final class IPv4FirstDns implements Dns {
        @Override
        public List<InetAddress> lookup(String hostname) throws java.net.UnknownHostException {
            List<InetAddress> rows = new ArrayList<>(Dns.SYSTEM.lookup(hostname));
            rows.sort(Comparator.comparingInt(value -> value instanceof Inet4Address ? 0 : 1));
            return rows;
        }
    }

    private static String esc(String value) {
        if (value == null) return "";
        return value
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t");
    }

    private static String classify(String body) {
        // Challenge JavaScript shipped by a normal site is not a challenge page.
        String lower = body == null ? "" : body.toLowerCase(java.util.Locale.ROOT);
        String clean = lower
            .replaceAll("(?s)<!--[\\s\\S]*?-->", " ")
            .replaceAll("(?s)<(script|style|noscript|template)\\b[^>]*>[\\s\\S]*?</\\1\\s*>", " ");
        java.util.regex.Matcher match = java.util.regex.Pattern
            .compile("(?s)<title\\b[^>]*>(.*?)</title\\s*>").matcher(clean);
        String title = match.find() ? match.group(1).replaceAll("<[^>]+>", " ") : "";
        String visible = clean.replaceAll("<[^>]+>", " ").replaceAll("\\s+", " ").trim();
        boolean titleChallenge = title.contains("just a moment")
            || title.contains("checking your browser")
            || title.contains("verify you are human")
            || title.contains("attention required");
        boolean visibleChallenge = visible.length() < 2000
            && (visible.contains("checking your browser")
                || visible.contains("verify you are human")
                || visible.contains("checking if the site connection is secure"));
        boolean structuralChallenge = visible.length() < 500
            && (clean.contains("challenge-platform") || clean.contains("cf-browser-verification"));
        if (titleChallenge || visibleChallenge || structuralChallenge)
            return "okhttp_jvm_challenge_persisted";
        if (visible.length() < 80) return "okhttp_jvm_inconclusive";
        return "okhttp_jvm_content_reached";
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 1 && "--self-test".equals(args[0])) {
            String ordinary = "<html><script>var lib='challenge-platform turnstile captcha just a moment';</script>"
                + "<body>" + "regular catalogue data ".repeat(12) + "</body></html>";
            String challenge = "<html><title>Just a moment...</title>"
                + "<body><div id='challenge-platform'>checking your browser</div></body></html>";
            if (!"okhttp_jvm_content_reached".equals(classify(ordinary))
                || !"okhttp_jvm_challenge_persisted".equals(classify(challenge))
                || !"okhttp_jvm_inconclusive".equals(classify("<html></html>"))) {
                throw new IllegalStateException("NuvioTV OkHttp DOM classification self-test failed");
            }
            System.out.println("FIELD_WAF_OKHTTP_CLASSIFIER_SELFTEST=passed");
            return;
        }
        if (args.length < 4) {
            throw new IllegalArgumentException(
                "usage: WafOkHttpProbe <url> <attempts> <timeoutSeconds> <defaultUserAgent> [safe-header...]"
            );
        }
        String url = args[0];
        int attempts = Math.max(1, Math.min(3, Integer.parseInt(args[1])));
        String profile = System.getenv().getOrDefault("NIAKVIO_WAF_OKHTTP_PROFILE", "nuvio-tv-okhttp-jvm").trim();
        String proxyMode = System.getenv().getOrDefault("NIAKVIO_WAF_PROXY_MODE", "no-proxy").trim();
        int profileMaxTimeout = Math.max(2, Math.min(60, Integer.parseInt(System.getenv().getOrDefault("NIAKVIO_WAF_MAX_TIMEOUT_SECONDS", "30"))));
        int timeout = Math.max(2, Math.min(profileMaxTimeout, Integer.parseInt(args[2])));
        String userAgent = args[3];
        Map<String, String> requestHeaders = new LinkedHashMap<>();
        for (int index = 4; index < args.length; index++) {
            String raw = args[index] == null ? "" : args[index];
            int separator = raw.indexOf(':');
            if (separator <= 0) continue;
            String name = raw.substring(0, separator).trim().toLowerCase(Locale.ROOT);
            String value = raw.substring(separator + 1).trim();
            if (!SAFE_REQUEST_HEADERS.contains(name) || name.equals("accept-encoding") || value.isEmpty()) continue;
            requestHeaders.put(name, value.length() > 500 ? value.substring(0, 500) : value);
        }

        OkHttpClient.Builder clientBuilder = new OkHttpClient.Builder()
            .dns(new IPv4FirstDns())
            .connectTimeout(timeout, TimeUnit.SECONDS)
            .readTimeout(timeout, TimeUnit.SECONDS)
            .writeTimeout(timeout, TimeUnit.SECONDS)
            .followRedirects(true)
            .followSslRedirects(true);
        final String proxyPolicy;
        if ("no-proxy".equals(proxyMode)) {
            clientBuilder.proxy(Proxy.NO_PROXY);
            proxyPolicy = "Proxy.NO_PROXY";
        } else if ("system".equals(proxyMode)) {
            proxyPolicy = "JVM/system default";
        } else {
            throw new IllegalArgumentException("unsupported NIAKVIO_WAF_PROXY_MODE");
        }
        OkHttpClient client = clientBuilder.build();

        List<String> attemptJson = new ArrayList<>();
        String finalOutcome = "okhttp_jvm_error";
        for (int attempt = 1; attempt <= attempts; attempt++) {
            Request.Builder requestBuilder = new Request.Builder().url(url);
            for (Map.Entry<String, String> header : requestHeaders.entrySet()) {
                requestBuilder.header(header.getKey(), header.getValue());
            }
            if (!requestHeaders.containsKey("user-agent")) {
                requestBuilder.header("User-Agent", userAgent);
            }
            Request request = requestBuilder.get().build();
            int status = 0;
            String outcome;
            String error = "";
            try (Response response = client.newCall(request).execute()) {
                status = response.code();
                // Never allocate or retain an entire media body for diagnostics.
                String body = response.body() == null ? "" : response.peekBody(262144).string();
                outcome = classify(body);
                if ((status < 200 || status >= 400)
                    && !"okhttp_jvm_challenge_persisted".equals(outcome)) {
                    outcome = "okhttp_jvm_http_error";
                }
            } catch (java.net.SocketTimeoutException timeoutError) {
                outcome = "okhttp_jvm_timeout";
                error = timeoutError.getClass().getSimpleName();
            } catch (Exception ex) {
                outcome = "okhttp_jvm_error";
                error = ex.getClass().getSimpleName();
            }
            attemptJson.add(
                "{\"attempt\":" + attempt +
                ",\"outcome\":\"" + esc(outcome) + "\"" +
                ",\"status\":" + status +
                (error.isEmpty() ? "" : ",\"error\":\"" + esc(error) + "\"") +
                "}"
            );
            finalOutcome = outcome;
            if ("okhttp_jvm_content_reached".equals(outcome)) break;
        }

        System.out.println(
            "NIAKVIO_WAF_OKHTTP={" +
            "\"profile\":\"" + esc(profile) + "\"," +
            "\"transportApproximation\":\"GitHub JVM OkHttp 4.12.0 audited Nuvio client transport profile\"," +
            "\"outcome\":\"" + esc(finalOutcome) + "\"," +
            "\"attemptCount\":" + attemptJson.size() + "," +
            "\"attempts\":[" + String.join(",", attemptJson) + "]," +
            "\"nativeContractApproximation\":{" +
              "\"httpStack\":\"OkHttp 4.12.0\"," +
              "\"proxyPolicy\":\"" + esc(proxyPolicy) + "\"," +
              "\"dnsPolicy\":\"IPv4FirstDns\"," +
              "\"redirects\":\"HTTP+SSL enabled\"," +
              "\"tlsRuntime\":\"GitHub JVM, not Android Conscrypt/device TLS\"," +
              "\"safeRequestHeaderCount\":" + requestHeaders.size() +
            "}" +
            "}"
        );
    }
}

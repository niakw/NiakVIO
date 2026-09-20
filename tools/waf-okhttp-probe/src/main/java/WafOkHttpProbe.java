import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.Proxy;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.TimeUnit;
import okhttp3.Dns;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public final class WafOkHttpProbe {
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
            .replace("\\\"", "\\\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t");
    }

    private static String classify(String body) {
        String lower = body == null ? "" : body.toLowerCase();
        for (String marker : CHALLENGE_MARKERS) {
            if (lower.contains(marker)) return "okhttp_jvm_challenge_persisted";
        }
        String text = lower.replaceAll("<[^>]+>", " ").replaceAll("\\s+", " ").trim();
        if (text.length() < 80) return "okhttp_jvm_inconclusive";
        return "okhttp_jvm_content_reached";
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 4) {
            throw new IllegalArgumentException("usage: WafOkHttpProbe <url> <attempts> <timeoutSeconds> <userAgent>");
        }
        String url = args[0];
        int attempts = Math.max(1, Math.min(3, Integer.parseInt(args[1])));
        int timeout = Math.max(2, Math.min(60, Integer.parseInt(args[2])));
        String userAgent = args[3];

        OkHttpClient client = new OkHttpClient.Builder()
            .dns(new IPv4FirstDns())
            .connectTimeout(timeout, TimeUnit.SECONDS)
            .readTimeout(timeout, TimeUnit.SECONDS)
            .writeTimeout(timeout, TimeUnit.SECONDS)
            .followRedirects(true)
            .followSslRedirects(true)
            .proxy(Proxy.NO_PROXY)
            .build();

        List<String> attemptJson = new ArrayList<>();
        String finalOutcome = "okhttp_jvm_error";
        for (int attempt = 1; attempt <= attempts; attempt++) {
            Request request = new Request.Builder()
                .url(url)
                .header("User-Agent", userAgent)
                .get()
                .build();
            int status = 0;
            String outcome;
            String error = "";
            try (Response response = client.newCall(request).execute()) {
                status = response.code();
                String body = response.body() == null ? "" : response.body().string();
                outcome = classify(body);
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
            "\"profile\":\"nuvio-tv-okhttp-jvm\"," +
            "\"transportApproximation\":\"GitHub JVM OkHttp 4.12.0 with NuvioTV PluginRuntime network policy\"," +
            "\"outcome\":\"" + esc(finalOutcome) + "\"," +
            "\"attemptCount\":" + attemptJson.size() + "," +
            "\"attempts\":[" + String.join(",", attemptJson) + "]," +
            "\"nativeContractApproximation\":{" +
              "\"httpStack\":\"OkHttp 4.12.0\"," +
              "\"proxyPolicy\":\"Proxy.NO_PROXY\"," +
              "\"dnsPolicy\":\"IPv4FirstDns\"," +
              "\"redirects\":\"HTTP+SSL enabled\"," +
              "\"tlsRuntime\":\"GitHub JVM, not Android Conscrypt/device TLS\"" +
            "}" +
            "}"
        );
    }
}

package com.guoneng.examprep;

import android.content.Context;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URLDecoder;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * 极简静态文件服务：把应用本体以 {@code http://127.0.0.1:<端口>/} 提供，供 WebView 加载。
 *
 * 应用本体在 APK 内是**单个 ASCII 名归档** {@code assets/www.zip}
 * （aapt2 在 Windows 上无法打开中文文件名的资产，故不逐文件打包；
 *  且集中成 zip 后读取更快）。首次启动时把该归档复制到应用私有目录，
 * 再用 {@link ZipFile} 随机访问，因此中文路径（docs、可选导入）也能正常提供。
 *
 * 安全约束：只监听回环地址、只读归档内条目、拒绝含 {@code ..} 或空字节的路径、
 * 仅支持 GET。
 */
final class AssetServer {

    private static final String BUNDLE = "www.zip";
    private static final String BUNDLE_ID = "www.id";
    private static final String LOCAL_ID = "www.id";

    private static final Map<String, String> MIME = new HashMap<String, String>();

    static {
        MIME.put("html", "text/html; charset=utf-8");
        MIME.put("htm", "text/html; charset=utf-8");
        MIME.put("js", "application/javascript; charset=utf-8");
        MIME.put("mjs", "application/javascript; charset=utf-8");
        MIME.put("css", "text/css; charset=utf-8");
        MIME.put("json", "application/json; charset=utf-8");
        MIME.put("webmanifest", "application/manifest+json; charset=utf-8");
        MIME.put("svg", "image/svg+xml");
        MIME.put("png", "image/png");
        MIME.put("jpg", "image/jpeg");
        MIME.put("jpeg", "image/jpeg");
        MIME.put("gif", "image/gif");
        MIME.put("ico", "image/x-icon");
        MIME.put("woff2", "font/woff2");
        MIME.put("md", "text/markdown; charset=utf-8");
        MIME.put("txt", "text/plain; charset=utf-8");
        MIME.put("csv", "text/csv; charset=utf-8");
    }

    private final ZipFile zip;
    private final ExecutorService pool = Executors.newFixedThreadPool(8);
    private ServerSocket server;
    private Thread acceptor;
    private volatile boolean running;

    AssetServer(Context context) throws IOException {
        this.zip = openBundle(context);
    }

    /** 把 APK 内的归档同步到私有目录（仅在内容版本变化时复制），并打开它。 */
    private static ZipFile openBundle(Context context) throws IOException {
        File dir = context.getFilesDir();
        File target = new File(dir, BUNDLE);

        String remoteId = readAssetText(context, BUNDLE_ID);
        File idFile = new File(dir, LOCAL_ID);
        String localId = idFile.isFile() ? readText(idFile) : "";

        if (!target.isFile() || !remoteId.equals(localId)) {
            File tmp = new File(dir, BUNDLE + ".tmp");
            InputStream in = context.getAssets().open(BUNDLE);
            try {
                OutputStream out = new BufferedOutputStream(new FileOutputStream(tmp), 128 * 1024);
                try {
                    byte[] buf = new byte[128 * 1024];
                    int n;
                    while ((n = in.read(buf)) != -1) {
                        out.write(buf, 0, n);
                    }
                } finally {
                    out.close();
                }
            } finally {
                in.close();
            }
            if (target.isFile() && !target.delete()) {
                throw new IOException("无法替换旧归档：" + target);
            }
            if (!tmp.renameTo(target)) {
                throw new IOException("无法就位归档：" + tmp);
            }
            writeText(idFile, remoteId);
        }
        return new ZipFile(target);
    }

    private static String readAssetText(Context context, String name) throws IOException {
        InputStream in = context.getAssets().open(name);
        try {
            return new String(readAll(in), "UTF-8").trim();
        } finally {
            in.close();
        }
    }

    private static String readText(File f) {
        try {
            InputStream in = new BufferedInputStream(new java.io.FileInputStream(f));
            try {
                return new String(readAll(in), "UTF-8").trim();
            } finally {
                in.close();
            }
        } catch (IOException e) {
            return "";
        }
    }

    private static void writeText(File f, String text) {
        try {
            OutputStream out = new FileOutputStream(f);
            try {
                out.write(text.getBytes("UTF-8"));
            } finally {
                out.close();
            }
        } catch (IOException ignored) {
            // 版本标记写不进去只是下次会再复制一遍，不影响功能
        }
    }

    /** 启动服务并返回实际端口（仅 127.0.0.1，端口由系统分配）。 */
    int start() throws IOException {
        server = new ServerSocket(0, 64, InetAddress.getByName("127.0.0.1"));
        running = true;
        acceptor = new Thread(new Runnable() {
            @Override
            public void run() {
                loop();
            }
        }, "asset-acceptor");
        acceptor.setDaemon(true);
        acceptor.start();
        return server.getLocalPort();
    }

    void stop() {
        running = false;
        try {
            if (server != null) server.close();
        } catch (IOException ignored) {
        }
        pool.shutdownNow();
        try {
            zip.close();
        } catch (IOException ignored) {
        }
    }

    private void loop() {
        while (running) {
            final Socket client;
            try {
                client = server.accept();
            } catch (IOException e) {
                break;      // 服务器已关闭
            }
            try {
                pool.execute(new Runnable() {
                    @Override
                    public void run() {
                        handle(client);
                    }
                });
            } catch (RuntimeException e) {
                closeQuietly(client);
            }
        }
    }

    private void handle(Socket client) {
        try {
            InputStream in = new BufferedInputStream(client.getInputStream());
            String requestLine = readLine(in);
            String header;
            while ((header = readLine(in)) != null && header.length() > 0) {
                // 请求头无需处理
            }

            OutputStream out = new BufferedOutputStream(client.getOutputStream());
            if (requestLine == null || requestLine.trim().length() == 0) {
                writeError(out, 400, "Bad Request");
                return;
            }

            String[] parts = requestLine.trim().split(" ");
            if (parts.length < 2 || !"GET".equalsIgnoreCase(parts[0])) {
                writeError(out, 405, "Method Not Allowed");
                return;
            }

            String path = normalize(parts[1]);
            if (path == null) {
                writeError(out, 403, "Forbidden");
                return;
            }

            byte[] body = readEntry(path);
            if (body == null) {
                writeError(out, 404, "Not Found");
                return;
            }

            StringBuilder head = new StringBuilder(160);
            head.append("HTTP/1.1 200 OK\r\n");
            head.append("Content-Type: ").append(guessMime(path)).append("\r\n");
            head.append("Content-Length: ").append(body.length).append("\r\n");
            head.append("Cache-Control: no-cache\r\n");
            head.append("Connection: close\r\n\r\n");
            out.write(head.toString().getBytes("UTF-8"));
            out.write(body);
            out.flush();
        } catch (IOException ignored) {
            // 客户端提前断开等，忽略
        } finally {
            closeQuietly(client);
        }
    }

    /** 读取归档内条目；不存在或是目录时返回 null。 */
    private byte[] readEntry(String path) throws IOException {
        ZipEntry entry = zip.getEntry(path);
        if (entry == null || entry.isDirectory()) {
            // 兼容“目录请求”→ index.html
            ZipEntry idx = zip.getEntry(path + "/index.html");
            if (idx == null || idx.isDirectory()) return null;
            entry = idx;
        }
        InputStream in = zip.getInputStream(entry);
        try {
            return readAll(in);
        } finally {
            in.close();
        }
    }

    /** 归一化请求路径；含 {@code ..} 或空字节时返回 null（拒绝）。 */
    private static String normalize(String raw) {
        String path = raw;
        int q = path.indexOf('?');
        if (q >= 0) path = path.substring(0, q);
        int h = path.indexOf('#');
        if (h >= 0) path = path.substring(0, h);
        try {
            path = URLDecoder.decode(path, "UTF-8");
        } catch (Exception ignored) {
        }
        if (path.indexOf('\0') >= 0 || path.indexOf("..") >= 0) return null;
        while (path.startsWith("/")) path = path.substring(1);
        if (path.length() == 0) path = "index.html";
        return path;
    }

    private static String guessMime(String path) {
        int dot = path.lastIndexOf('.');
        if (dot < 0 || dot == path.length() - 1) return "application/octet-stream";
        String ext = path.substring(dot + 1).toLowerCase(Locale.US);
        String mime = MIME.get(ext);
        return mime == null ? "application/octet-stream" : mime;
    }

    private static void writeError(OutputStream out, int code, String message) throws IOException {
        byte[] body = (code + " " + message + "\n").getBytes("UTF-8");
        String head = "HTTP/1.1 " + code + " " + message + "\r\n"
                + "Content-Type: text/plain; charset=utf-8\r\n"
                + "Content-Length: " + body.length + "\r\n"
                + "Connection: close\r\n\r\n";
        out.write(head.getBytes("UTF-8"));
        out.write(body);
        out.flush();
    }

    private static String readLine(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream(128);
        int ch;
        boolean any = false;
        while ((ch = in.read()) != -1) {
            any = true;
            if (ch == '\n') break;
            if (ch != '\r') buf.write(ch);
            if (buf.size() > 8192) break;
        }
        if (!any && buf.size() == 0) return null;
        return new String(buf.toByteArray(), "UTF-8");
    }

    private static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream buf = new ByteArrayOutputStream(64 * 1024);
        byte[] chunk = new byte[64 * 1024];
        int n;
        while ((n = in.read(chunk)) != -1) {
            buf.write(chunk, 0, n);
        }
        return buf.toByteArray();
    }

    private static void closeQuietly(Socket s) {
        try {
            s.close();
        } catch (IOException ignored) {
        }
    }
}

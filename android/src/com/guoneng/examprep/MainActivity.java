package com.guoneng.examprep;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.KeyEvent;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.IOException;

/**
 * 离线备考 APP 的外壳：用 WebView 承载应用本体。
 *
 * 应用本体（题库、知识库、9 份报告、可选导入包）打包在 APK 的
 * {@code assets/www.zip} 内，由内置 {@link AssetServer} 通过
 * {@code http://127.0.0.1:<随机端口>/} 提供。
 *
 * 为什么不用 file:// 直接打开：
 *   file:// 源在 Android WebView 里 IndexedDB 常被禁用、Service Worker 无法注册；
 *   而 http://127.0.0.1 属于安全上下文，应用的「IndexedDB → localStorage → 内存」
 *   三级降级与 sw.js 离线缓存都能正常工作，退到后台再回来答题进度也不丢。
 *
 * 失败不静默：归档解包或端口分配失败时会直接在界面上说明原因，而不是白屏。
 */
public class MainActivity extends Activity {

    private static final String TAG = "GuonengExam";

    private WebView web;
    private AssetServer server;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int port = -1;
        String failure = null;
        try {
            server = new AssetServer(this);
            port = server.start();
        } catch (IOException e) {
            failure = e.toString();
            Log.e(TAG, "应用数据准备失败", e);
            if (server != null) {
                server.stop();
                server = null;
            }
        }

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);          // localStorage / sessionStorage
        s.setDatabaseEnabled(true);            // WebSQL 与部分存储能力
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setSupportZoom(true);
        s.setBuiltInZoomControls(false);       // 允许双指缩放但不显示缩放按钮
        s.setDisplayZoomControls(false);
        s.setTextZoom(100);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        web.setBackgroundColor(0xFFF6F7F9);

        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return route(request.getUrl());
            }

            @Override
            @SuppressWarnings("deprecation")
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return route(Uri.parse(url));
            }
        });

        setContentView(web);

        if (port > 0) {
            web.loadUrl("http://127.0.0.1:" + port + "/index.html");
        } else {
            String html = "<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\">"
                    + "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                    + "<body style=\"font-family:system-ui,-apple-system,sans-serif;padding:24px;line-height:1.7\">"
                    + "<h2>应用数据未能准备完成</h2>"
                    + "<p>题库归档（assets/www.zip）解包失败，应用无法启动。这不是“没有内容”，"
                    + "而是本机存储或安装包异常，请重装应用；若反复出现请反馈下面这行信息。</p>"
                    + "<pre style=\"white-space:pre-wrap;background:#f2f4f7;padding:12px;border-radius:8px\">"
                    + escape(failure == null ? "未知原因" : failure) + "</pre></body></html>";
            web.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null);
        }
    }

    /** 只把本机应用页面留在 WebView 内；外部链接（报告里的来源网址）交给系统浏览器。 */
    private boolean route(Uri uri) {
        if (uri == null) return false;
        String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase();
        String host = uri.getHost() == null ? "" : uri.getHost();
        if ("http".equals(scheme) || "https".equals(scheme)) {
            if ("127.0.0.1".equals(host) || "localhost".equals(host)) return false;   // 内部：正常加载
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, uri));
            } catch (Exception ignored) {
                // 没有可用浏览器时保持原样，不影响应用本体
            }
            return true;
        }
        // file:// 等其它协议一律不放行（应用内容已由内置服务提供）
        return !"about".equals(scheme);
    }

    private static String escape(String text) {
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && web != null && web.canGoBack()) {
            web.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        if (server != null) server.stop();
        if (web != null) {
            web.stopLoading();
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}

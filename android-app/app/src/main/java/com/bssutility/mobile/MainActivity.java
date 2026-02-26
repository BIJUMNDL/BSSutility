package com.bssutility.mobile;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.CookieManager;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private ValueCallback<Uri[]> filePathCallback;

    private ActivityResultLauncher<Intent> fileChooserLauncher;

    private static final String INSPECTION_PATH = "/new/";
    private static final String DIESEL_PATH = "/diesel/new/";
    private static final String MIGRATIONS_PATH = "/transmedia/migrations/";

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button btnInspection = findViewById(R.id.btnInspection);
        Button btnDiesel = findViewById(R.id.btnDiesel);
        Button btnMigrations = findViewById(R.id.btnMigrations);
        webView = findViewById(R.id.webView);

        fileChooserLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (filePathCallback == null) {
                        return;
                    }
                    Uri[] results = null;
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        Uri dataUri = result.getData().getData();
                        if (dataUri != null) {
                            results = new Uri[]{dataUri};
                        }
                    }
                    filePathCallback.onReceiveValue(results);
                    filePathCallback = null;
                }
        );

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setBuiltInZoomControls(false);

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(@NonNull WebView view, @NonNull WebResourceRequest request) {
                view.loadUrl(request.getUrl().toString());
                return true;
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(
                    WebView webView,
                    ValueCallback<Uri[]> filePathCallback,
                    FileChooserParams fileChooserParams
            ) {
                if (MainActivity.this.filePathCallback != null) {
                    MainActivity.this.filePathCallback.onReceiveValue(null);
                }

                MainActivity.this.filePathCallback = filePathCallback;
                Intent intent = fileChooserParams.createIntent();
                fileChooserLauncher.launch(intent);
                return true;
            }
        });

        btnInspection.setOnClickListener(v -> loadModulePath(INSPECTION_PATH));
        btnDiesel.setOnClickListener(v -> loadModulePath(DIESEL_PATH));
        btnMigrations.setOnClickListener(v -> loadModulePath(MIGRATIONS_PATH));

        if (savedInstanceState == null) {
            loadModulePath(INSPECTION_PATH);
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    private void loadModulePath(String path) {
        String base = BuildConfig.BASE_URL;
        String url = base.endsWith("/")
                ? base.substring(0, base.length() - 1) + path
                : base + path;
        webView.loadUrl(url);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }
}

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteStaticCopy } from "vite-plugin-static-copy";

// https://vitejs.dev/config/
export default defineConfig({
    base: "/DSI/",
    plugins: [
        react(),
        viteStaticCopy({
            targets: [
                {
                    src: "node_modules/pdfjs-dist/build/pdf.worker.mjs",
                    dest: ""
                },
                {
                    src: "node_modules/pdfjs-dist/build/pdf.worker.mjs.map",
                    dest: ""
                }
            ]
        })
    ],
    // define: {
    //     global: {}
    //   },
    build: {
        // outDir: "../backend/static",
        outDir: "..//frontend/build",
        emptyOutDir: true,
        sourcemap: true,
        rollupOptions: {
            output: {
                manualChunks: id => {
                    
                    if (id.includes("@fluentui/react-icons")) {
                        return "fluentui-icons";
                    } else if (id.includes("@fluentui/react")) {
                        return "fluentui-react";
                    } else if (id.includes("node_modules")) {
                        return "vendor";
                    }
                    
                }
            }
        }
    },
    resolve: {
        alias: {
          // Fix for potential issues with ESM modules
          "pdfjs-dist/build/pdf.worker.mjs": "node_modules/pdfjs-dist/build/pdf.worker.mjs",
        },
      },

    server: {
        proxy: {
            "/ask": "http://127.0.0.1:5000/",
            "/chat": "http://127.0.0.1:5000/",
            "/chat_stream": "http://127.0.0.1:5000/",
            "/upload": "http://127.0.0.1:5000/",
            "/api/auth": "http://127.0.0.1:5000",
            "/delete-folder": "http://127.0.0.1:5000",
            "/lang_sel": "http://127.0.0.1:5000",
            "/doctranslate": "http://127.0.0.1:5000",
            "/process-sharepoint-files": "http://127.0.0.1:5000",
            "/get-sharepoint-file-list": "http://127.0.0.1:5000"
        }
    }
});

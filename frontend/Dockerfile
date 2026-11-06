# This complete, verified toolchain is also used for production static builds.
FROM node:24.22.2-trixie-slim@sha256:0820eaa85e07d0490446dd01d14707e17e6108a36988cf374899cd057eb3812d AS toolchain
RUN node --input-type=module -e 'import {createHash} from "node:crypto"; import {writeFileSync} from "node:fs"; const response = await fetch("https://registry.npmjs.org/npm/-/npm-11.21.2.tgz", {redirect: "error", signal: AbortSignal.timeout(60000)}); if (!response.ok) throw new Error("npm download failed"); const archive = Buffer.from(await response.arrayBuffer()); if (createHash("sha512").update(archive).digest("base64") !== "7HPApk+AflMUavSseL1Pm6CnYqMIHk53x+KmuhqmTDqPkjPMgxIpTPcTqsE91EKNw4gFBJV9fnXiSdGm1DXq9A==") throw new Error("npm integrity mismatch"); writeFileSync("/tmp/npm.tgz", archive);' \
    && rm -rf /usr/local/lib/node_modules/npm \
    && mkdir /usr/local/lib/node_modules/npm \
    && tar -xzf /tmp/npm.tgz --strip-components=1 -C /usr/local/lib/node_modules/npm \
    && rm /tmp/npm.tgz \
    && test "$(npm --version)" = 11.21.2

FROM toolchain AS dev

WORKDIR /app
RUN chown node:node /app
USER node

COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

COPY --chown=node:node . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]

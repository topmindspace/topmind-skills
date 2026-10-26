import { readFileSync, appendFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

export function resolveRelease({ eventName, refName, inputTag, version, packageVersion }) {
  if (!/^\d+\.\d+\.\d+$/.test(version) || version !== packageVersion) {
    throw new Error("Pack and npm package must have the same numeric release version");
  }
  const tag = eventName === "workflow_dispatch" ? inputTag : refName;
  if (tag !== `v${version}`) throw new Error(`Release tag must equal v${version}`);
  return { version, tag };
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const result = resolveRelease({
    eventName: process.env.GITHUB_EVENT_NAME,
    refName: process.env.GITHUB_REF_NAME,
    inputTag: process.env.INPUT_RELEASE_TAG,
    version: JSON.parse(readFileSync("topmind-pack.json", "utf8")).version,
    packageVersion: JSON.parse(readFileSync("package.json", "utf8")).version,
  });
  appendFileSync(process.env.GITHUB_OUTPUT, `version=${result.version}\ntag=${result.tag}\n`);
}

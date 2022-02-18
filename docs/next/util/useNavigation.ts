import masterNavigation from "../../content/_navigation.json";
import { useVersion } from "./useVersion";
import versionedNavigation from "../.versioned_content/_versioned_navigation.json";

export function flatten(yx: any) {
  const xs = JSON.parse(JSON.stringify(yx));

  return xs.reduce((acc: any, x: any) => {
    acc = acc.concat(x);
    if (x.children) {
      acc = acc.concat(flatten(x.children));
      x.children = [];
    }
    return acc;
  }, []);
}

export const useNavigation = () => {
  const { version } = useVersion();

  if (version === "master") {
    return masterNavigation;
  }

  return versionedNavigation[version];
};

export const latestAllPaths = () => {
  // Master
  return flatten(masterNavigation)
    .filter((n: { path: any }) => n.path)
    .map(({ path }) => path.split("/").splice(1))
    .map((page: string[]) => {
      return {
        params: {
          page: page,
        },
      };
    });
};

export const allPaths = () => {
  let paths = [];

  // Master
  const flattenedMasterNavigation = flatten(masterNavigation)
    .filter((n: { path: any }) => n.path)
    .map(({ path }) => path.split("/").splice(1))
    .map((page: string[]) => {
      return {
        params: {
          page: ["master", ...page],
        },
      };
    });

  paths = [...flattenedMasterNavigation, ...paths];

  // enable versioning when on Vercel production or explicitly asked to
  if (process.env.VERCEL_ENV === "production" || __VERSIONING_ENABLED__) {
    for (const [key, value] of Object.entries(versionedNavigation)) {
      const flattenedVersionNavigation = flatten(value)
        .filter((n: { path: any }) => n.path)
        .map(({ path }) => [key, ...path.split("/").splice(1)])
        .map((page: string[]) => {
          return {
            params: {
              page: page,
            },
          };
        });

      paths = [...paths, ...flattenedVersionNavigation];
    }
  }

  return paths;
};

export const navigations = {
  masterNavigation,
  versionedNavigation,
};

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // This project is in a monorepo-like structure with frontend as subfolder
  // The root package.json is for promptfoo testing only
  // To silence the multiple lockfiles warning, we explicitly set this as standalone
};

export default nextConfig;

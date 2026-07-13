/** @type {import('next').NextConfig} */
// output: 'export' produces a fully static site (HTML/CSS/JS) in ./out,
// which we host on S3 + CloudFront. Data is fetched client-side from the API.
const nextConfig = {
  output: "export",
};

export default nextConfig;

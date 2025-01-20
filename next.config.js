/** @type {import('next').NextConfig} */
const nextConfig = {
  rewrites: async () => {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/api/:path*"
            : "http://localhost:8000/api/:path*",
      },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: process.env.NODE_ENV === "development" ? 'http' : 'https',
        hostname: process.env.NODE_ENV === "development" ? 'localhost' : process.env.NEXT_PUBLIC_HOST || 'your-domain.com',
        port: process.env.NODE_ENV === "development" ? '8000' : '',
        pathname: '/uploads/**',
      },
    ],
  },
};

module.exports = nextConfig;

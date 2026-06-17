import { NextRequest, NextResponse } from "next/server";

export function proxy(request: NextRequest) {

  const token =
    request.cookies.get("token")?.value;

  const pathname =
    request.nextUrl.pathname;

  const publicRoutes = [
    "/",
    "/login",
    "/register",
  ];

  const isPublicRoute =
    publicRoutes.includes(pathname);

  // User not logged in
  if (!token && !isPublicRoute) {

    return NextResponse.redirect(
      new URL(
        "/login",
        request.url
      )
    );
  }

  // User already logged in
  if (
    token &&
    (
      pathname === "/login" ||
      pathname === "/register"
    )
  ) {

    return NextResponse.redirect(
      new URL(
        "/dashboard",
        request.url
      )
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/onboarding/:path*",
    "/companions/:path*",
    "/chat/:path*",
    "/profile/:path*",
    "/settings/:path*",
    "/login",
    "/register",
  ],
};
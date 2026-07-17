"use client";

import {
    createContext,
    useContext,
    useRef
} from "react";

const AvatarContext = createContext<any>(null);

export function AvatarProvider({
    children
}: {
    children: React.ReactNode;
}) {

    const sessionRef = useRef<any>(null);

    return (
        <AvatarContext.Provider
            value={{
                sessionRef
            }}
        >
            {children}
        </AvatarContext.Provider>
    );
}

export function useAvatar() {
    return useContext(
        AvatarContext
    );
}
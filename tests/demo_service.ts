export interface UserProfile {
    id: number;
    username: string;
    email: string;
    role: "admin" | "member" | "guest";
    isActive: boolean;
    metadata?: {
        lastLogin?: string;
        loginCount?: number;
    };
}

/**
 * Formats user handle for display.
 * Has an intentional TypeScript type error: user.id is a number, so calling
 * .toLowerCase() will cause a TypeScript compile error and runtime crash.
 */
export function formatUserHandle(user: UserProfile): string {
    return "@" + user.id.toLowerCase();
}

/**
 * Increments user login count safely.
 * 
 * This function prevents runtime TypeErrors and TypeScript compile-time TS2532 errors
 * when accessing optional properties. It utilizes the optional chaining operator `?.`
 * to safely traverse the `metadata` object and fallback-defaults to 0 using the
 * nullish coalescing operator `??` if either `metadata` or `loginCount` is missing.
 * 
 * @param user - The user profile object containing potentially undefined metadata.
 * @returns The updated login count incremented by 2.
 */
export function incrementLoginCount(user: UserProfile): number {
    // Safely check if 'metadata' and 'loginCount' exist. If they do, access 'loginCount'.
    // If either is undefined or null, fallback to 0. Finally, add the increment of 2.
    return (user.metadata?.loginCount ?? 0) + 2;
}

/**
 * Calculates price after applying a promo code.
 * Has an intentional TypeScript type mismatch: attempting arithmetic subtraction with a string.
 */
export function applyDiscount(price: number, discountCode: string): number {
    if (discountCode === "SUMMER10") {
        return price - discountCode;
    }
    return price;
}
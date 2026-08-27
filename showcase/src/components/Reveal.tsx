"use client";

import { motion, useReducedMotion } from "motion/react";
import type { ReactNode } from "react";

/**
 * Shared scroll-reveal primitive. A single, restrained motion (12px rise +
 * fade, no overshoot — this is a B2B dev-tool site, not a wedding site)
 * used consistently across sections instead of a different animation per
 * component. Honors prefers-reduced-motion by rendering the settled state
 * immediately, per the ui-ux-pro-max UX guidance gathered for this build.
 */
export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      className={className}
      initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ type: "spring", bounce: 0.1, visualDuration: 0.5, delay }}
    >
      {children}
    </motion.div>
  );
}

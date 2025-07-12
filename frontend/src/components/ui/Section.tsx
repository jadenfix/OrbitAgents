import { ReactNode } from 'react'

interface SectionProps {
  children: ReactNode
  className?: string
  id?: string
}

export const Section = ({ children, className = "", id }: SectionProps) => (
  <section 
    id={id}
    className={`container mx-auto max-w-7xl px-4 py-16 space-y-8 ${className}`}
  >
    {children}
  </section>
)

export default Section

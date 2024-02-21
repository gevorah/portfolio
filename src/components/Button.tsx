import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef, type ButtonHTMLAttributes } from 'react';

const buttonVariants = cva(
  [
    'inline-flex justify-center items-center whitespace-nowrap',
    'rounded-lg text-sm font-medium transition-colors ',
    'focus-visible:ring-offset-2 focus-visible:outline-none focus-visible:ring-1',
    'disabled:pointer-events-none disabled:opacity-50'
  ],
  {
    variants: {
      variant: {
        default: '',
        outlined: [
          'hover:bg-secondary-1 hover:text-primary-1',
          'dark:hover:bg-primary-1 dark:hover:text-secondary-1'
        ]
      },
      size: {
        default: '',
        icon: 'h-9 w-9'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default'
    }
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };

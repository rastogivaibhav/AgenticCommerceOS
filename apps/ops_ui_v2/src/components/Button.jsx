import { forwardRef } from 'react';
import { cva } from 'class-variance-authority';
import { cn } from '../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 font-medium transition-colors focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        filled:      'bg-primary text-on-primary hover:opacity-90 rounded-[20px]',
        tonal:       'bg-secondary-container text-on-secondary-container hover:opacity-90 rounded-[20px]',
        outlined:    'border border-outline text-primary hover:bg-surface-variant rounded-[20px]',
        text:        'text-primary hover:bg-surface-variant rounded-[20px]',
        // Legacy aliases so existing code using variant="default"/"ghost"/"outline" doesn't break
        default:     'bg-primary text-on-primary hover:opacity-90 rounded-[20px]',
        ghost:       'text-on-surface hover:bg-surface-variant rounded-[20px]',
        outline:     'border border-outline text-primary hover:bg-surface-variant rounded-[20px]',
        destructive: 'bg-error text-on-error hover:opacity-90 rounded-[20px]',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-5 text-sm',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: {
      variant: 'filled',
      size: 'md',
    },
  }
);

const Button = forwardRef(({ className, variant, size, ...props }, ref) => (
  <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
));

Button.displayName = 'Button';
export default Button;

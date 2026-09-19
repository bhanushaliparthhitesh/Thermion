import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ScreenType, TransitionDirection } from './types';
import { InitialScreen } from './components/InitialScreen';
import { OperatorConsole } from './components/OperatorConsole';

export default function App() {
  const [screen, setScreen] = useState<ScreenType>('initial');
  const [direction, setDirection] = useState<TransitionDirection>('push');

  const navigateToConsole = () => {
    setDirection('push');
    setScreen('console');
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  const navigateToInitial = () => {
    setDirection('push_back');
    setScreen('initial');
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  // Push transition variants
  const pageVariants = {
    initial: (dir: TransitionDirection) => ({
      x: dir === 'push' ? '100%' : '-30%',
      opacity: dir === 'push' ? 1 : 0.8,
      position: 'absolute' as const,
      top: 0,
      left: 0,
      right: 0,
      width: '100%',
      zIndex: dir === 'push' ? 2 : 1,
    }),
    animate: {
      x: '0%',
      opacity: 1,
      position: 'relative' as const,
      width: '100%',
      zIndex: 2,
      transition: {
        x: { type: 'spring' as const, stiffness: 280, damping: 30 },
        opacity: { duration: 0.25 },
      },
    },
    exit: (dir: TransitionDirection) => ({
      x: dir === 'push' ? '-30%' : '100%',
      opacity: dir === 'push' ? 0.6 : 1,
      position: 'absolute' as const,
      top: 0,
      left: 0,
      right: 0,
      width: '100%',
      zIndex: dir === 'push' ? 1 : 2,
      transition: {
        x: { type: 'spring' as const, stiffness: 280, damping: 30 },
        opacity: { duration: 0.25 },
      },
    }),
  };

  return (
    <div className="min-h-screen bg-surface-canvas text-on-surface relative overflow-x-hidden">
      <AnimatePresence custom={direction} mode="wait">
        {screen === 'initial' ? (
          <motion.div
            key="screen-initial"
            custom={direction}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="w-full min-h-screen"
          >
            <InitialScreen onNavigateToConsole={navigateToConsole} />
          </motion.div>
        ) : (
          <motion.div
            key="screen-console"
            custom={direction}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="w-full min-h-screen"
          >
            <OperatorConsole onNavigateToInitial={navigateToInitial} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

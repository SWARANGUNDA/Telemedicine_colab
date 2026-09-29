import React from 'react';
import { getActiveUserAvatar, getAvatarById, svgToDataUri, hasUserUpdatedProfile } from '../../utils/avatarCatalog';

export function Avatar({ src, avatarId, user, alt = 'Avatar', name = '', size = 'md', className = '' }) {
  const sizeStyles = {
    sm: "w-8 h-8 text-xs",
    md: "w-10 h-10 text-sm",
    lg: "w-14 h-14 text-base",
    xl: "w-28 h-28 text-xl"
  };

  const getInitials = (n) => {
    if (!n) return 'U';
    const parts = n.trim().split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return n.substring(0, 2).toUpperCase();
  };

  // Determine if profile/avatar has been explicitly updated by user
  let isProfileUpdated = false;
  if (user?.avatar) isProfileUpdated = true;
  if (avatarId) isProfileUpdated = true;
  if (src) isProfileUpdated = true;
  if (user && hasUserUpdatedProfile(user)) isProfileUpdated = true;

  let imageSrc = src;
  if (isProfileUpdated) {
    if (!imageSrc && avatarId) {
      const av = getAvatarById(avatarId);
      if (av) imageSrc = av.url || svgToDataUri(av.svg);
    }

    if (!imageSrc) {
      const active = getActiveUserAvatar(user);
      if (active) imageSrc = active.srcUrl || active.url || svgToDataUri(active.svg);
    }
  }

  const displayName = name || user?.full_name || user?.name || user?.email || 'User';

  return (
    <div className={`relative inline-flex items-center justify-center rounded-full bg-gradient-to-tr from-slate-800 via-indigo-900 to-blue-900 shadow-md overflow-hidden shrink-0 ring-2 ring-white/20 ${sizeStyles[size] || sizeStyles.md} ${className}`}>
      {imageSrc && isProfileUpdated ? (
        <img
          src={imageSrc}
          alt={alt}
          className="w-full h-full object-cover select-none transition-transform hover:scale-105"
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      ) : (
        <span className="font-extrabold text-white tracking-wider font-sans select-none">{getInitials(displayName)}</span>
      )}
    </div>
  );
}

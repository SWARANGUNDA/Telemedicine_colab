// High-Resolution Studio Ghibli Indian Anime Avatars Catalog
// Supports Role-Gated Avatars: Patients (Boy, Girl, Men, Women, Old Man, Old Woman), Doctors, & Administrator.

export const AVATAR_CATALOG = [
  // --- PATIENT AVATARS (INDIAN GHIBLI ANIME ART STYLE) ---
  {
    id: 'boy',
    label: 'Boy Patient',
    role: 'Boy',
    category: 'PATIENT',
    color: 'from-sky-500 to-cyan-600',
    ring: 'ring-sky-400',
    url: '/avatars/boy.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="64" fill="#0EA5E9"/>
      <circle cx="64" cy="54" r="24" fill="#FDBA74"/>
    </svg>`
  },
  {
    id: 'girl',
    label: 'Girl Patient',
    role: 'Girl',
    category: 'PATIENT',
    color: 'from-fuchsia-500 to-pink-600',
    ring: 'ring-fuchsia-400',
    url: '/avatars/girl.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="64" fill="#D946EF"/>
      <circle cx="64" cy="54" r="23" fill="#FED7AA"/>
    </svg>`
  },
  {
    id: 'male',
    label: 'Male Patient',
    role: 'Men',
    category: 'PATIENT',
    color: 'from-emerald-600 to-teal-700',
    ring: 'ring-emerald-400',
    url: '/avatars/male.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="64" fill="#059669"/>
      <circle cx="64" cy="52" r="26" fill="#FDBA74"/>
    </svg>`
  },
  {
    id: 'female',
    label: 'Female Patient',
    role: 'Women',
    category: 'PATIENT',
    color: 'from-rose-500 to-red-600',
    ring: 'ring-rose-400',
    url: '/avatars/female.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="64" fill="#E11D48"/>
      <circle cx="64" cy="54" r="24" fill="#FED7AA"/>
    </svg>`
  },
  {
    id: 'old_man',
    label: 'Senior Man',
    role: 'Old Man',
    category: 'PATIENT',
    color: 'from-amber-600 to-yellow-700',
    ring: 'ring-amber-400',
    url: '/avatars/old_man.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="64" fill="#D97706"/>
      <circle cx="64" cy="54" r="25" fill="#FDBA74"/>
    </svg>`
  },
  {
    id: 'old_woman',
    label: 'Senior Woman',
    role: 'Old Woman',
    category: 'PATIENT',
    color: 'from-teal-600 to-cyan-700',
    ring: 'ring-teal-400',
    url: '/avatars/old_woman.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="64" fill="#0D9488"/>
      <circle cx="64" cy="54" r="24" fill="#FED7AA"/>
    </svg>`
  },

  // --- DOCTOR AVATARS (INDIAN GHIBLI ANIME ART STYLE) ---
  {
    id: 'doctor_male',
    label: 'Doctor (Male)',
    role: 'Doctor - Male',
    category: 'DOCTOR',
    color: 'from-blue-600 to-indigo-700',
    ring: 'ring-blue-400',
    url: '/avatars/doctor_male.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="64" fill="#2563EB"/>
      <circle cx="64" cy="48" r="24" fill="#FDBA74"/>
    </svg>`
  },
  {
    id: 'doctor_female',
    label: 'Doctor (Female)',
    role: 'Doctor - Female',
    category: 'DOCTOR',
    color: 'from-purple-600 to-pink-700',
    ring: 'ring-purple-400',
    url: '/avatars/doctor_female.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="64" cy="64" r="64" fill="#9333EA"/>
      <circle cx="64" cy="48" r="23" fill="#FED7AA"/>
    </svg>`
  },

  // --- ADMIN AVATAR (INDIAN GHIBLI ANIME ART STYLE) ---
  {
    id: 'admin',
    label: 'Administrator',
    role: 'Administrator',
    category: 'ADMIN',
    color: 'from-slate-700 to-blue-900',
    ring: 'ring-slate-400',
    url: '/avatars/admin.png',
    svg: `<svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="128" height="128" rx="64" fill="#0F172A"/>
    </svg>`
  }
];

// Helper: Convert SVG string to Data URI for <img> tags
export function svgToDataUri(svgString) {
  return `data:image/svg+xml;utf8,${encodeURIComponent(svgString)}`;
}

// Get avatar object by ID
export function getAvatarById(id) {
  if (!id) return AVATAR_CATALOG[2]; // Default to 'male' / Men
  const searchId = String(id).toLowerCase();
  const found = AVATAR_CATALOG.find(a => a.id === searchId || a.role.toLowerCase() === searchId || a.label.toLowerCase() === searchId);
  return found || AVATAR_CATALOG[2]; // Default to 'male' / Men
}

// Filter available avatars based on User Role (PATIENT cannot see Doctor/Admin avatars)
export function getAvailableAvatarsForRole(role = 'PATIENT') {
  const r = (role || 'PATIENT').toUpperCase();
  if (r === 'DOCTOR') {
    return AVATAR_CATALOG.filter(a => a.category === 'DOCTOR');
  }
  if (r === 'ADMIN') {
    return AVATAR_CATALOG.filter(a => a.category === 'ADMIN' || a.category === 'DOCTOR');
  }
  // PATIENT Role: STRICTLY Patients ONLY (Boy, Girl, Men, Women, Old Man, Old Woman)
  return AVATAR_CATALOG.filter(a => a.category === 'PATIENT');
}

// Helper to check if user has updated their profile/avatar preferences
export function hasUserUpdatedProfile(user) {
  if (!user) return false;
  if (user.avatar) return true;
  const userId = user.user_id || 'guest';
  try {
    const saved = localStorage.getItem(`telemed_user_profile_${userId}`);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.isUpdated || parsed.selectedAvatar) return true;
    }
  } catch (e) {}
  return false;
}

// Helper to get active user's avatar image URL or SVG Data URI
export function getActiveUserAvatar(user) {
  let savedId = null;
  const userId = user?.user_id || 'guest';
  try {
    const saved = localStorage.getItem(`telemed_user_profile_${userId}`) || localStorage.getItem('telemed_user_profile');
    if (saved) {
      const parsed = JSON.parse(saved);
      savedId = parsed.selectedAvatar;
    }
  } catch (e) {}

  const role = (user?.role || 'PATIENT').toUpperCase();
  const defaultId = role === 'ADMIN' ? 'admin' : role === 'DOCTOR' ? 'doctor_male' : 'male';
  const targetId = savedId || user?.avatar || defaultId;
  const avatarObj = getAvatarById(targetId);

  return {
    ...avatarObj,
    srcUrl: avatarObj.url || svgToDataUri(avatarObj.svg)
  };
}

import React, { useState } from 'react';
import PublicCanvasLayout from '../components/landing/PublicCanvasLayout';
import { Sparkles, Mail, Send, CheckCircle2, Headphones, Globe, Share2, Code, Phone, MapPin } from 'lucide-react';

export default function ContactPage({ user, onOpenAuth }) {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    subject: '',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!formData.fullName.trim() || !formData.email.trim() || !formData.message.trim()) {
      setErrorMsg('Please fill in your name, email, and message.');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
      setFormData({ fullName: '', email: '', subject: '', message: '' });
    }, 1000);
  };

  return (
    <PublicCanvasLayout user={user} onOpenAuth={onOpenAuth}>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-16">
        
        {/* HEADER & 2-COLUMN CONTACT LAYOUT */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          
          {/* LEFT COLUMN: Contact Information */}
          <div className="lg:col-span-5 space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-sm font-bold shadow-2xs">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Contact Us</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.1]">
              We’d Love to <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
                Hear From You
              </span>
            </h1>
            
            <p className="text-base text-slate-600 font-medium leading-relaxed">
              Have questions, collaboration ideas or support requests? Get in touch with us.
            </p>

            <div className="space-y-4 pt-2">
              <div className="p-4 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-xl bg-blue-50 text-blue-600 shrink-0">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-extrabold text-slate-900">Email</h4>
                  <p className="text-sm text-slate-600 font-medium">hello@telemedai.com</p>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-xl bg-blue-50 text-blue-600 shrink-0">
                  <Phone className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-extrabold text-slate-900">Phone</h4>
                  <p className="text-sm text-slate-600 font-medium">+91 98765 43210</p>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-sm flex items-center gap-4">
                <div className="p-3 rounded-xl bg-blue-50 text-blue-600 shrink-0">
                  <MapPin className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-extrabold text-slate-900">Address</h4>
                  <p className="text-sm text-slate-600 font-medium">123 AI Health Way, San Francisco, CA 94107, USA</p>
                </div>
              </div>
            </div>

            {/* Follow Us Social Links */}
            <div className="pt-2">
              <h4 className="text-xs font-black text-slate-900 uppercase tracking-wider mb-3">Follow Us</h4>
              <div className="flex items-center gap-3">
                <a href="https://github.com/SWARANGUNDA/TeleMed" target="_blank" rel="noopener noreferrer" className="p-3.5 rounded-2xl bg-white border border-slate-200/90 text-slate-700 hover:text-blue-600 hover:shadow transition-all">
                  <Code className="w-5 h-5" />
                </a>
                <a href="#" className="p-3.5 rounded-2xl bg-white border border-slate-200/90 text-slate-700 hover:text-blue-600 hover:shadow transition-all">
                  <Globe className="w-5 h-5" />
                </a>
                <a href="#" className="p-3.5 rounded-2xl bg-white border border-slate-200/90 text-slate-700 hover:text-blue-600 hover:shadow transition-all">
                  <Share2 className="w-5 h-5" />
                </a>
              </div>
            </div>

          </div>

          {/* RIGHT COLUMN: Contact Form */}
          <div className="lg:col-span-7">
            <div className="p-8 sm:p-10 rounded-3xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-xl space-y-6">
              
              <div>
                <h3 className="text-xl sm:text-2xl font-extrabold text-slate-900">Send us a message</h3>
              </div>

              {submitted ? (
                <div className="p-6 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 space-y-2 text-center">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                  <h4 className="text-base sm:text-lg font-extrabold">Message Sent Successfully!</h4>
                  <p className="text-sm font-medium">Thank you for reaching out. We will respond shortly.</p>
                  <button
                    onClick={() => setSubmitted(false)}
                    className="mt-3 px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-bold text-sm shadow hover:bg-emerald-700"
                  >
                    Send Another Message
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  {errorMsg && (
                    <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-bold">
                      {errorMsg}
                    </div>
                  )}

                  <div className="space-y-1.5 text-left">
                    <label className="text-xs sm:text-sm font-extrabold text-slate-700">Full Name</label>
                    <input
                      type="text"
                      name="fullName"
                      value={formData.fullName}
                      onChange={handleChange}
                      placeholder="Full Name"
                      className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all"
                    />
                  </div>

                  <div className="space-y-1.5 text-left">
                    <label className="text-xs sm:text-sm font-extrabold text-slate-700">Email Address</label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="Email Address"
                      className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all"
                    />
                  </div>

                  <div className="space-y-1.5 text-left">
                    <label className="text-xs sm:text-sm font-extrabold text-slate-700">Subject</label>
                    <input
                      type="text"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      placeholder="Subject"
                      className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all"
                    />
                  </div>

                  <div className="space-y-1.5 text-left">
                    <label className="text-xs sm:text-sm font-extrabold text-slate-700">Your Message</label>
                    <textarea
                      name="message"
                      rows={4}
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="Your Message"
                      className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all resize-none"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="py-4 px-8 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-extrabold text-sm sm:text-base shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2.5 cursor-pointer disabled:opacity-75"
                  >
                    {loading ? (
                      <span>Sending...</span>
                    ) : (
                      <>
                        <span>Send Message</span>
                        <Send className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>
              )}

            </div>
          </div>

        </div>

        {/* BOTTOM SUPPORT INDICATOR */}
        <div className="p-6 sm:p-8 rounded-3xl bg-blue-50/90 border border-blue-200/90 flex items-center justify-between gap-4 flex-wrap">
          <div className="space-y-1">
            <h4 className="text-base sm:text-lg font-extrabold text-slate-900">We typically respond within 24 hours.</h4>
            <p className="text-xs sm:text-sm text-slate-600 font-medium">Your inquiries are important to us.</p>
          </div>
          <div className="p-3.5 rounded-2xl bg-blue-600 text-white shrink-0 shadow-md">
            <Headphones className="w-7 h-7" />
          </div>
        </div>

      </main>
    </PublicCanvasLayout>
  );
}

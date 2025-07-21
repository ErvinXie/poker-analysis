#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json

class LanguageManager:
    """Language manager for internationalization support"""
    
    def __init__(self, default_language='en'):
        self.default_language = default_language
        self.current_language = default_language
        self.languages = {}
        self.locales_dir = 'locales'
        self.load_languages()
    
    def load_languages(self):
        """Load all available language files"""
        if not os.path.exists(self.locales_dir):
            print(f"Warning: locales directory '{self.locales_dir}' not found")
            return
        
        # Load available language files
        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                lang_code = filename[:-5]  # Remove .json extension
                lang_file = os.path.join(self.locales_dir, filename)
                
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.languages[lang_code] = json.load(f)
                    print(f"Loaded language: {lang_code}")
                except Exception as e:
                    print(f"Error loading language file {lang_file}: {e}")
    
    def set_language(self, language):
        """Set the current language"""
        if language in self.languages:
            self.current_language = language
            print(f"Language set to: {language}")
        else:
            print(f"Language '{language}' not available, using default: {self.default_language}")
            self.current_language = self.default_language
    
    def get_text(self, key, **kwargs):
        """Get localized text by key with optional formatting parameters"""
        # Try current language first
        text = self._get_text_from_lang(self.current_language, key)
        
        # Fallback to default language if not found
        if text is None and self.current_language != self.default_language:
            text = self._get_text_from_lang(self.default_language, key)
        
        # Final fallback to the key itself
        if text is None:
            print(f"Warning: Text key '{key}' not found in any language")
            text = key
        
        # Format with parameters if provided
        if kwargs and isinstance(text, str):
            try:
                text = text.format(**kwargs)
            except Exception as e:
                print(f"Error formatting text '{text}' with params {kwargs}: {e}")
        
        return text
    
    def _get_text_from_lang(self, language, key):
        """Get text from specific language by dotted key notation"""
        if language not in self.languages:
            return None
        
        # Navigate through nested dictionary using dot notation
        keys = key.split('.')
        current = self.languages[language]
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return None
    
    def get_available_languages(self):
        """Get list of available languages"""
        return list(self.languages.keys())
    
    def get_current_language(self):
        """Get current language code"""
        return self.current_language

# Global instance
_language_manager = None

def get_language_manager():
    """Get the global language manager instance"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager

def set_language(language):
    """Convenience function to set language globally"""
    get_language_manager().set_language(language)

def get_text(key, **kwargs):
    """Convenience function to get localized text"""
    return get_language_manager().get_text(key, **kwargs)
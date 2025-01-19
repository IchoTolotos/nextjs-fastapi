'use client';

import { useState, useEffect } from 'react';
import ImageUpload from './components/ImageUpload';
import SearchBar from './components/SearchBar';
import ImageGrid from './components/ImageGrid';

interface ImageResult {
  id: string;
  filename: string;
  similarity?: number;
}

export default function Home() {
  const [images, setImages] = useState<ImageResult[]>([]);
  const [loading, setLoading] = useState(false);

  const loadImages = async () => {
    try {
      const response = await fetch('/api/images');
      if (!response.ok) throw new Error('Failed to fetch images');
      const data = await response.json();
      setImages(data);
    } catch (error) {
      console.error('Error loading images:', error);
    }
  };

  useEffect(() => {
    loadImages();
  }, []);

  const handleSearch = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/images/search?query=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Search failed');
      const results = await response.json();
      setImages(results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (deletedId: string) => {
    setImages(images.filter(img => img.id !== deletedId));
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Semantic Image Search
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Upload images and search through them using natural language
          </p>
        </div>

        <div className="space-y-8">
          <div className="max-w-xl mx-auto">
            <ImageUpload onUploadSuccess={loadImages} />
          </div>

          <div className="flex justify-center">
            <SearchBar onSearch={handleSearch} />
          </div>

          {loading ? (
            <div className="text-center py-8">
              <div className="text-gray-600">Searching...</div>
            </div>
          ) : (
            <ImageGrid images={images} onDelete={handleDelete} />
          )}
        </div>
      </div>
    </div>
  );
}

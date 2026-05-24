import api from './api';

export const feedbackService = {
  /**
   * Fetches aggregate rating statistics from the backend.
   * @returns {Promise<{ average_rating: number, total_ratings: number }>}
   */
  async getRatings() {
    const response = await api.get('/api/ratings');
    return response.data;
  },

  /**
   * Submits a rating with optional textual comments.
   * @param {number} rating - Star count between 1 and 5
   * @param {string} [comment] - Optional textual comment
   */
  async submitRating(rating, comment = '') {
    const response = await api.post('/api/ratings', { rating, comment });
    return response.data;
  },

  /**
   * Sends a contact message query.
   * @param {string} name - Sender's name
   * @param {string} email - Sender's email
   * @param {string} message - Message body
   */
  async sendContactMessage(name, email, message) {
    const response = await api.post('/api/contact', { name, email, message });
    return response.data;
  }
};

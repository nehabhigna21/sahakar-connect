import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../../api";
import StatusBadge from "../../components/StatusBadge";
import StarRating from "../../components/StarRating";

export default function MyBookings() {
  const [bookings, setBookings] = useState([]);
  const [reviewedIds, setReviewedIds] = useState(new Set());
  const [ratingFormFor, setRatingFormFor] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  function refresh() {
    api.listMyBookings().then(setBookings);
    api.listMyReviews().then((reviews) => setReviewedIds(new Set(reviews.map((r) => r.booking_id))));
  }

  useEffect(refresh, []);

  async function handleComplete(id) {
    await api.completeBooking(id);
    refresh();
  }

  async function handleSubmitRating(bookingId) {
    if (rating === 0) return;
    await api.createReview({ booking_id: bookingId, rating, comment });
    setRatingFormFor(null);
    setRating(0);
    setComment("");
    refresh();
  }

  return (
    <section className="card">
      <h1 className="page-title">My bookings</h1>
      <ul className="list">
        {bookings.map((b) => (
          <li key={b.id}>
            <div className="booking-row">
              <div>
                <strong>#{b.id}</strong> · Rs.{b.price}
                {b.is_emergency && <span className="tag">emergency</span>}
              </div>
              <StatusBadge status={b.status} />
            </div>
            {b.match_reason && <div className="muted">{b.match_reason}</div>}
            <div className="actions">
              {b.status === "matched" && (
                <button onClick={() => handleComplete(b.id)}>Mark completed</button>
              )}
              {b.status === "completed" && !reviewedIds.has(b.id) && ratingFormFor !== b.id && (
                <button onClick={() => setRatingFormFor(b.id)}>Rate this booking</button>
              )}
              {b.status === "completed" && reviewedIds.has(b.id) && (
                <span className="muted">Rated, thank you.</span>
              )}
              <Link to={`/grievances?booking_id=${b.id}`}>
                <button className="danger">File a grievance</button>
              </Link>
            </div>
            {ratingFormFor === b.id && (
              <div className="rating-form">
                <StarRating value={rating} onChange={setRating} />
                <textarea
                  placeholder="Optional comment"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                />
                <button onClick={() => handleSubmitRating(b.id)}>Submit rating</button>
              </div>
            )}
          </li>
        ))}
        {bookings.length === 0 && <li className="muted">No bookings yet.</li>}
      </ul>
    </section>
  );
}

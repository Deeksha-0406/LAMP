import React from 'react';
import './AboutUs.css';
 
const AboutUs = () => {
  return (
    <div className="about-us">
      <h1>About Us</h1>
      <section className="mission">
        <h2>Our Mission</h2>
        <p>
          We aim to revolutionize the employee management landscape by offering innovative solutions that simplify and enhance the way organizations manage their workforce. Our commitment to excellence drives us to continuously improve and adapt our platform to meet the evolving needs of our clients.
        </p>
      </section>
      <section className="team">
        <h2>Meet the Team</h2>
        <div className="team-member">
          <h3>Jane Smith</h3>
          <p>CEO & Founder</p>
        </div>
        <div className="team-member">
          <h3>Mike Johnson</h3>
          <p>CTO</p>
        </div>
        <div className="team-member">
          <h3>Emily Davis</h3>
          <p>Lead Developer</p>
        </div>
      </section>
      <section className="contact">
        <h2>Contact Us</h2>
        <p>If you have any questions or need support, feel free to reach out to us:</p>
        <p>Email: <a href="mailto:support@example.com">support@example.com</a></p>
        <p>Phone: <a href="tel:+1234567890">123-456-7890</a></p>
      </section>
    </div>
  );
};
 
export default AboutUs;